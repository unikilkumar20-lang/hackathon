# Firebase Authentication Setup Guide for RippleGuard

RippleGuard uses **Firebase Authentication exclusively** for user identity management (sign-in, registration, password reset, and Google OAuth).

> [!IMPORTANT]
> **Architecture Decision:**
> - Firebase is used **ONLY for authentication**.
> - All application state, projects, assets, snapshots, graphs, runs, and advisories are stored in **PostgreSQL**.
> - **Never** enable or use Firestore, Firebase Realtime Database, Firebase Storage, Firebase Hosting, or Firebase Functions.
> - Protected endpoints fail closed (HTTP 401) whenever Firebase is unconfigured or a token is invalid.
> - Real service credentials must never be committed to source control or exposed with `NEXT_PUBLIC_` prefixes.

---

## 1. Create a Firebase Project

1. Navigate to the [Firebase Console](https://console.firebase.google.com/).
2. Click **Add project** (or select an existing project).
3. Name your project (e.g. `rippleguard-dev`).
4. Google Analytics can be enabled or disabled according to your preference.
5. Click **Create Project**.

---

## 2. Enable Authentication Providers

1. In your Firebase Project overview, navigate to **Build** → **Authentication**.
2. Click **Get Started**.
3. Under the **Sign-in method** tab, configure:
   - **Email/Password**:
     - Click on **Email/Password**.
     - Toggle **Enable** to ON.
     - (Optional) Enable Email link passwordless sign-in if desired.
     - Click **Save**.
   - **Google**:
     - Click on **Google**.
     - Toggle **Enable** to ON.
     - Select your project support email.
     - Click **Save**.

---

## 3. Configure Authorized Domains

In **Authentication** → **Settings** → **Authorized domains**, ensure the following domains are listed:
- `localhost` (added by default)
- `127.0.0.1`
- Any custom domain used when deploying the Next.js frontend

---

## 4. Obtain Frontend Web Credentials

1. In your Firebase project settings (click the Gear icon ⚙️ next to *Project Overview* → **Project settings**).
2. Under the **General** tab, scroll down to **Your apps**.
3. Click the **Web** icon (`</>`) to register a web application (e.g., `rippleguard-web`).
4. Firebase will present your configuration values.
5. Create `apps/web/.env.local` by copying `apps/web/.env.example`:

```bash
cp apps/web/.env.example apps/web/.env.local
```

6. Fill in the values:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSy...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_APP_ID=1:1234567890:web:abcdef...
```

---

## 5. Obtain Backend Admin Credentials

The backend FastAPI service verifies ID tokens using the Firebase Admin SDK.

1. In **Project settings** ⚙️, navigate to the **Service accounts** tab.
2. Under **Firebase Admin SDK**, select **Python**.
3. Click **Generate new private key**, then click **Generate key**.
4. Securely download the JSON key file to a safe location **outside the repository** (e.g., `~/.config/rippleguard/service-account.json`).
5. In `services/api/.env` (copy from `services/api/.env.example`):

```dotenv
APP_ENV=development
DATABASE_URL=postgresql+psycopg://rippleguard:local_password@localhost:5432/rippleguard
FIREBASE_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/outside/repo/service-account.json
CORS_ORIGINS=http://localhost:3000
```

> [!NOTE]
> If `GOOGLE_APPLICATION_CREDENTIALS` is omitted, Firebase Admin can also verify tokens using Google's public x509 certificates and the configured `FIREBASE_PROJECT_ID` directly.

---

## 6. Verification and Fail-Closed Behavior

- When `FIREBASE_PROJECT_ID` is missing or placeholder (`replace_me`), all protected endpoints (`/api/v1/me`, `/api/v1/projects`, etc.) return:
  ```json
  {
    "error": {
      "code": "FIREBASE_AUTH_UNCONFIGURED",
      "message": "Authentication backend is unconfigured (FIREBASE_PROJECT_ID required). Protected endpoints fail closed.",
      "details": [],
      "request_id": "..."
    }
  }
  ```
- Public endpoints (`/health`, `/ready`, `/demo`) continue to function without authentication.
