import os
import json
import logging
from typing import Optional, Dict, Any
from fastapi import Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials as firebase_credentials

from app.core.config import settings
from app.core.errors import UnauthorizedException
from app.db.session import get_db
from app.db.models import User

logger = logging.getLogger("rippleguard.auth")

security = HTTPBearer(auto_error=False)

# Initialize Firebase Admin once if configuration exists
_firebase_initialized = False


def initialize_firebase_admin() -> bool:
    global _firebase_initialized
    if _firebase_initialized:
        return True

    project_id = settings.FIREBASE_PROJECT_ID.strip()
    if not project_id or project_id == "replace_me":
        logger.warning("FIREBASE_PROJECT_ID is not configured. Protected endpoints will fail closed.")
        return False

    try:
        cred_path = settings.GOOGLE_APPLICATION_CREDENTIALS.strip()
        if cred_path and os.path.isfile(cred_path):
            cred = firebase_credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {"projectId": project_id})
        else:
            # Initialize with project ID (uses ADC or token verification via Google public keys)
            firebase_admin.initialize_app(options={"projectId": project_id})
        _firebase_initialized = True
        logger.info(f"Firebase Admin initialized for project: {project_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin: {e}")
        return False


def verify_firebase_id_token(token: str) -> Dict[str, Any]:
    """Verify Firebase ID token.
    Fails closed if Firebase is unconfigured or token is invalid.
    Allows synthetic test tokens ONLY when AUTH_ALLOW_MOCK_TOKENS_FOR_TESTING is True.
    """
    # 1. Test-only bypass if explicitly enabled in test settings
    if settings.AUTH_ALLOW_MOCK_TOKENS_FOR_TESTING:
        if token.startswith("test-token-") or token.startswith("mock-token-"):
            parts = token.split(":", 1)
            uid = parts[0].replace("test-token-", "").replace("mock-token-", "")
            email = parts[1] if len(parts) > 1 else f"{uid}@example.com"
            return {
                "uid": uid,
                "sub": uid,
                "email": email,
                "name": f"Test User {uid}",
            }

    # 2. Check configuration - must fail closed
    project_id = settings.FIREBASE_PROJECT_ID.strip()
    if not project_id or project_id == "replace_me":
        raise UnauthorizedException(
            message="Authentication backend is unconfigured (FIREBASE_PROJECT_ID required). Protected endpoints fail closed.",
            code="FIREBASE_AUTH_UNCONFIGURED",
        )

    # 3. Ensure Firebase Admin is initialized
    if not _firebase_initialized and not initialize_firebase_admin():
        raise UnauthorizedException(
            message="Firebase Admin initialization failed. Protected endpoints fail closed.",
            code="FIREBASE_INIT_FAILED",
        )

    # 4. Verify token through Firebase Admin SDK or Google public certs
    decoded = None
    cred_path = settings.GOOGLE_APPLICATION_CREDENTIALS.strip()
    if cred_path and os.path.isfile(cred_path):
        try:
            decoded = firebase_auth.verify_id_token(token, check_revoked=False)
        except Exception as admin_err:
            logger.warning(f"Firebase admin token verification failed: {admin_err}")
            raise UnauthorizedException(message="Invalid, expired, or malformed Firebase ID token.")
    else:
        try:
            import google.oauth2.id_token as google_id_token
            import google.auth.transport.requests as google_requests
            request_adapter = google_requests.Request()
            raw_decoded = google_id_token.verify_firebase_token(token, request_adapter, audience=project_id)
            if raw_decoded:
                decoded = dict(raw_decoded)
                decoded["uid"] = raw_decoded.get("user_id") or raw_decoded.get("sub")
        except Exception as cert_err:
            logger.warning(f"Firebase token verification failed: {cert_err}")
            raise UnauthorizedException(message="Invalid, expired, or malformed Firebase ID token.")

    if not decoded:
        raise UnauthorizedException(message="Invalid, expired, or malformed Firebase ID token.")

    # Validate audience & issuer match our configured project ID
    if decoded.get("aud") != project_id:
        raise UnauthorizedException("Invalid token audience. Expected configured Firebase Project ID.")
    expected_iss = f"https://securetoken.google.com/{project_id}"
    if decoded.get("iss") != expected_iss:
        raise UnauthorizedException("Invalid token issuer.")
    if not decoded.get("uid"):
        raise UnauthorizedException("Token has no valid UID.")
    return decoded


def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency to extract and verify the Firebase user, then get/upsert local User."""
    if not auth_header or not auth_header.credentials:
        raise UnauthorizedException("Missing Authorization header with Bearer token.")

    token = auth_header.credentials.strip()
    claims = verify_firebase_id_token(token)

    firebase_uid = claims.get("uid") or claims.get("sub")
    if not firebase_uid:
        raise UnauthorizedException("Token payload missing user identifier.")

    email = claims.get("email")
    display_name = claims.get("name")

    # Upsert user record in PostgreSQL
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update email/display_name if changed
        updated = False
        if email and user.email != email:
            user.email = email
            updated = True
        if display_name and user.display_name != display_name:
            user.display_name = display_name
            updated = True
        if updated:
            db.commit()
            db.refresh(user)

    return user
