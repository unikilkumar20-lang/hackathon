import { initializeApp, getApps, getApp, FirebaseApp } from "firebase/app";
import {
  getAuth,
  Auth,
  GoogleAuthProvider as FBGoogleAuthProvider,
  signInWithPopup as fbSignInWithPopup,
  signInWithEmailAndPassword as fbSignInWithEmailAndPassword,
  createUserWithEmailAndPassword as fbCreateUserWithEmailAndPassword,
  signOut as fbSignOutReal,
  sendPasswordResetEmail as fbSendPasswordResetEmailReal,
  onAuthStateChanged as fbOnAuthStateChanged,
  User as RealFirebaseUser,
} from "firebase/auth";

export interface FirebaseUser {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL?: string | null;
  getIdToken: (forceRefresh?: boolean) => Promise<string>;
}

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "AIzaSyBVGDfN2RLnkTKfM8x2v4SLC_6JUocVMcM",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "ripple-guard.firebaseapp.com",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "ripple-guard",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "ripple-guard.firebasestorage.app",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "81571425592",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "1:81571425592:web:035980d2f44e12c43aa5cd",
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID || "G-NWD89HY3CN",
};

export function isFirebaseConfigured(): boolean {
  return Boolean(firebaseConfig.apiKey && firebaseConfig.projectId);
}

let app: FirebaseApp | null = null;
let auth: Auth | null = null;

if (typeof window !== "undefined") {
  try {
    app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
    auth = getAuth(app);
  } catch (err) {
    console.warn("Failed to initialize Firebase Auth:", err);
  }
}

export class GoogleAuthProvider extends FBGoogleAuthProvider {
  constructor() {
    super();
    this.setCustomParameters({ prompt: "select_account" });
  }
}

export async function signInWithPopup(authInstance: any, provider: any) {
  if (auth) {
    return fbSignInWithPopup(auth, provider);
  }
  throw new Error("Firebase Auth is not initialized");
}

export async function signInWithEmailAndPassword(authInstance: any, email: string, pass: string) {
  if (auth) {
    return fbSignInWithEmailAndPassword(auth, email, pass);
  }
  throw new Error("Firebase Auth is not initialized");
}

export async function createUserWithEmailAndPassword(authInstance: any, email: string, pass: string) {
  if (auth) {
    return fbCreateUserWithEmailAndPassword(auth, email, pass);
  }
  throw new Error("Firebase Auth is not initialized");
}

export async function fbSignOut(authInstance: any): Promise<void> {
  if (auth) {
    return fbSignOutReal(auth);
  }
}

export async function fbSendPasswordResetEmail(authInstance: any, email: string): Promise<void> {
  if (auth) {
    return fbSendPasswordResetEmailReal(auth, email);
  }
  throw new Error("Firebase Auth is not initialized");
}

export function onAuthStateChanged(authInstance: any, callback: (user: any) => void): () => void {
  if (auth) {
    return fbOnAuthStateChanged(auth, callback);
  }
  return () => {};
}

export { auth };
