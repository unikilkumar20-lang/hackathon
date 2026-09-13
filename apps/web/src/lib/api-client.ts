import { auth } from "./firebase-client";

export class ApiError extends Error {
  code: string;
  status: number;
  details: unknown[];

  constructor(
    code: string,
    message: string,
    status: number = 400,
    details: unknown[] = []
  ) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = (
    process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL
  ).replace(/\/+$/, "");

  // Ensure path starts with single slash
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  
  // If endpoint already includes /api/v1 prefix, strip to avoid doubling
  const targetPath = cleanEndpoint.startsWith("/api/v1")
    ? cleanEndpoint.replace("/api/v1", "")
    : cleanEndpoint;

  const url = `${baseUrl}${targetPath}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Attach Firebase ID token if authenticated
  let token: string | null = null;
  if (auth && auth.currentUser) {
    try {
      token = await auth.currentUser.getIdToken();
    } catch {
      // ignore
    }
  }

  // Support local development mock auth if running locally without Firebase credentials
  if (!token && typeof window !== "undefined") {
    const localDevUser = localStorage.getItem("rippleguard_dev_user");
    if (localDevUser) {
      token = `mock-token-${localDevUser}:dev@example.com`;
    }
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const fetchConfig: RequestInit = {
    ...options,
    headers,
  };

  let response = await fetch(url, fetchConfig);

  // Auto-retry once on 401 if token can be refreshed
  if (response.status === 401 && auth && auth.currentUser) {
    try {
      const refreshedToken = await auth.currentUser.getIdToken(true);
      if (refreshedToken) {
        headers.set("Authorization", `Bearer ${refreshedToken}`);
        response = await fetch(url, { ...fetchConfig, headers });
      }
    } catch {
      // proceed to standard error handling
    }
  }

  if (response.status === 204) {
    return null as unknown as T;
  }

  if (!response.ok) {
    let errCode = `HTTP_${response.status}`;
    let errMsg = `Request failed with status ${response.status}`;
    let details: unknown[] = [];

    try {
      const errorJson = await response.json();
      if (errorJson && errorJson.error) {
        errCode = errorJson.error.code || errCode;
        errMsg = errorJson.error.message || errMsg;
        details = errorJson.error.details || [];
      }
    } catch {
      // response body was not valid json
    }

    throw new ApiError(errCode, errMsg, response.status, details);
  }

  return (await response.json()) as T;
}
