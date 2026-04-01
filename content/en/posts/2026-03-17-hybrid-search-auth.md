---
image: "/images/posts/2026-03-17-hybrid-search-auth/cover-en.jpg"
title: "Hybrid Image Search Dev Log — Implementing the Google OAuth Login Wall"
description: "Adding Google OAuth to FastAPI and React, protecting the full API with JWT cookie-based authentication"
date: 2026-03-17
series: "hybrid-image-search-demo"
series_num: 1
last_commit: "8ccefef"
categories: ["dev-log"]
tags: ["hybrid-search", "google-oauth", "jwt", "fastapi", "react", "python"]
toc: true
math: false
---

## Overview

I added Google OAuth login to the hybrid image search demo app. The app previously had no authentication — every API endpoint was wide open. The image generation feature calls the Gemini API and incurs real costs, so leaving it unprotected wasn't an option. For this task, I ran the full cycle through the Claude Code superpowers plugin workflow: writing the design spec, spec review, implementation planning, coding, and security review. The result: 17 commits, a complete login wall.

<!--more-->

## Authentication Architecture

I went with **Lightweight Custom Auth** instead of a library. FastAPI-Users brings 15+ features I don't need (password reset, email verification, etc.), and Authlib + Session Middleware uses server-side redirects that don't fit a SPA architecture. Building it myself means I understand and can debug every line.

Core stack:
- **Backend**: `google-auth` (Google ID token verification) + `python-jose` (JWT creation/verification)
- **Frontend**: `@react-oauth/google` (Google Sign-In popup button)
- **Session**: JWT stored in HttpOnly cookie (more XSS-resistant than localStorage)

### Auth Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as React Frontend
    participant G as Google OAuth
    participant B as FastAPI Backend
    participant DB as SQLite

    U->>F: Open app
    F->>B: GET /api/auth/me
    B-->>F: 401 Unauthorized
    F->>U: Show LoginPage

    U->>F: Click Google Sign-In
    F->>G: OAuth popup
    G-->>F: Return ID Token

    F->>B: POST /api/auth/google&lt;br/&gt;{id_token}
    B->>G: verify_oauth2_token()
    G-->>B: Claims (sub, email, name, picture)
    B->>DB: get_or_create_user()
    DB-->>B: User object
    B->>B: create_jwt(user_id)
    B-->>F: Set-Cookie: access_token=JWT&lt;br/&gt;(HttpOnly, SameSite=Lax)
    B-->>F: LoginResponse {user}

    F->>U: Switch to main app

    Note over F,B: All subsequent requests

    F->>B: API request&lt;br/&gt;(cookie attached automatically)
    B->>B: get_current_user()&lt;br/&gt;JWT verification
    B-->>F: Protected data
```

## Database Changes

### Adding the User Model

The app previously had four tables — `SearchLog`, `ImageSelection`, `GenerationLog`, `ManualUpload` — all recording actions anonymously. I created a new `User` table and added a `user_id` FK column to all four.

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    google_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    picture_url = Column(String, nullable=True)
    generation_count = Column(Integer, default=0, nullable=False)
    last_active_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
```

I left existing data untouched. The FK columns are declared `nullable=True` so existing rows stay as `user_id=NULL`, and only new rows get a `user_id` filled by the auth middleware. One Alembic migration handled table creation and FK additions.

## Backend Implementation

### auth.py — Authentication Module

All auth logic lives in `backend/src/auth.py`. Three core functions:

**1. Google token verification** — `verify_google_token()`

```python
async def verify_google_token(token: str) -> dict:
    try:
        # verify_oauth2_token is synchronous and may fetch Google's public keys over the network
        idinfo = await asyncio.to_thread(
            id_token.verify_oauth2_token,
            token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        if idinfo["iss"] not in ("accounts.google.com", "https://accounts.google.com"):
            raise ValueError("Invalid issuer")
        return idinfo
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {e}",
        )
```

The security review flagged this: `verify_oauth2_token()` is synchronous and may perform a network I/O to fetch Google's public keys. Calling it without `asyncio.to_thread()` blocks the event loop.

**2. JWT cookie management** — `create_jwt()` / `set_auth_cookie()`

The JWT carries only `user_id` and `exp`. Key cookie settings:
- `HttpOnly` — JavaScript can't read the token, preventing XSS theft
- `SameSite=Lax` — CSRF protection (no extra CSRF token needed)
- `Secure` — Active in production (HTTPS) only, disabled for local development

**3. FastAPI Dependency** — `get_current_user()`

```python
async def get_current_user(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(access_token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Update last_active_at with throttling (once per minute)
    now = datetime.now(timezone.utc)
    if not user.last_active_at or (now - user.last_active_at).seconds > 60:
        await update_last_active(user.id)

    return user
```

Updating `last_active_at` on every request would put write pressure on SQLite, so it's throttled to once per minute. I also created a `get_optional_user()` variant that returns `None` instead of 401, for the `/api/auth/me` endpoint.

### Protecting Endpoints

I added `user = Depends(get_current_user)` to all 10 data-access endpoints. The image generation endpoint additionally calls `increment_generation_count(user.id)`. All logging functions (`log_search`, `log_image_selection`, etc.) received a `user_id` parameter and now store it in the DB.

```
# Protected (get_current_user required)
POST /search, /search/simple, /search/hybrid, GET /search
POST /api/generate-image, /api/log-selection, /api/upload-reference-image
GET /api/history/generations, /api/images, /api/images/{image_id}

# Unprotected (no auth required)
GET /, /health, /api/info, /images/{filename}
POST /api/auth/google, /api/auth/logout
GET /api/auth/me
```

## Frontend Login Flow

### LoginPage Component

I used `@react-oauth/google`'s `<GoogleLogin>` component for popup-based login. Rather than a redirect flow, a Google account selection in the popup returns an ID token directly via callback.

```tsx
// LoginPage.tsx
import { GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google';

function LoginPage({ onLogin }: { onLogin: (user: UserProfile) => void }) {
  const handleSuccess = async (credentialResponse) => {
    const response = await loginWithGoogle(credentialResponse.credential);
    onLogin(response.user);
  };

  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
      <div className="login-container">
        <h1>Hybrid Image Search</h1>
        <GoogleLogin onSuccess={handleSuccess} onError={() => setError('Login failed')} />
      </div>
    </GoogleOAuthProvider>
  );
}
```

### App.tsx Changes

Auth state is managed at the app entry point:

1. **On mount** — call `GET /api/auth/me`. Success restores the existing session; 401 shows the login page.
2. **Conditional rendering** — `authLoading` → spinner, `!user` → `<LoginPage>`, else → main UI
3. **Logout** — top-right button, calls `POST /api/auth/logout` then clears state
4. **Data loading guard** — `if (!user) return;` in `useEffect` prevents API calls before login

```tsx
// App.tsx (core logic)
useEffect(() => {
  if (!user) return;
  const loadHistory = async () => {
    const items = await fetchGenerationHistory(20, 0);
    setGeneratedImages(mapHistoryItems(items));
  };
  loadHistory();
}, [user]);
```

### api.ts — Axios Configuration

```typescript
// withCredentials: true — browser automatically attaches cookie to requests
const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
});

// 401 interceptor — redirect to login on token expiry
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.dispatchEvent(new Event('auth:logout'));
    }
    return Promise.reject(error);
  }
);
```

## Security Review

After implementation, I ran `/ship` for a security review. Key findings and fixes:

| Item | Problem | Fix |
|------|---------|-----|
| Google token verification | Sync function blocking event loop | Wrap with `asyncio.to_thread()` |
| JWT secret not set | All auth fails silently on startup without a secret | Log `logger.warning` in `configure_auth()` |
| `create_jwt()` guard | Signing attempted when `JWT_SECRET=None` | Add guard raising `RuntimeError` |
| Frontend styles | Hardcoded inline styles | Convert to Tailwind CSS classes |
| History loading | API calls attempted before login | Add `user` dependency guard |

Secret management was also considered up front. `GOOGLE_OAUTH_CLIENT_ID` and `JWT_SECRET` are loaded via `os.getenv()`, not from YAML config files. YAML is version-controlled, so secrets don't belong there. Only non-secret config like token expiry lives in `config.py`'s `AuthConfig`.

## Dev Tools: `/ship` Command and PostToolUse Hooks

I also set up project-specific dev tooling during this work.

**PostToolUse hook** — automatic type checking on every file edit:
- `.ts/.tsx` files modified → `tsc --noEmit` runs automatically
- `backend/*.py` files modified → `pyright` runs automatically

**`/ship` command** — six-step verification pipeline before each commit:
1. Identify changed files
2. Type validation (tsc + pyright)
3. API contract sync check (`schemas.py` ↔ `api.ts`)
4. Code simplification review
5. Security review
6. Auto-commit

One interesting debugging detour: the PostToolUse hook used `$CLAUDE_FILE_PATH` as an environment variable, but it didn't work. Turns out hooks receive input via **stdin JSON**:
```bash
INPUT=$(cat)
FILEPATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
```

## Commit Log

| Message | Key files |
|---------|-----------|
| docs: Google login design spec | `2026-03-17-google-login-design.md` |
| docs: incorporate spec review feedback | same |
| docs: fix endpoint path and description consistency | same |
| docs: write implementation plan | `2026-03-17-google-login.md` |
| feat: User model + user_id FK | `models.py`, Alembic migration |
| feat: google-auth, python-jose dependencies | `requirements.txt` |
| feat: @react-oauth/google dependency | `package.json` |
| feat: auth Pydantic schemas | `schemas.py` |
| feat: user CRUD and activity tracking | `service.py` |
| feat: auth module (token verification + JWT cookie) | `auth.py` |
| feat: AuthConfig | `config.py`, `default.yaml` |
| feat: LoginPage component | `LoginPage.tsx` |
| feat: auth API functions, 401 interceptor | `api.ts` |
| feat: auth state, login/logout flow | `App.tsx` |
| feat: auth endpoints + full route protection | `main.py`, `service.py` |
| fix: security guards, async token verification, UI | `auth.py`, `App.tsx` |
| feat: Google OAuth login wall complete | final merge |

## Insights

**HttpOnly cookie vs. localStorage** — Many tutorials store JWTs in localStorage, but one XSS hit and the token is gone. HttpOnly cookies are completely inaccessible to JavaScript. When protecting a paid service like the Gemini API, this is the right choice. The implementation overhead over localStorage is basically just adding `allow_credentials=True` to the CORS config.

**Design first, code later** — This session followed the sequence: design spec → review → implementation plan → review → coding. It seems slower, but the spec review caught missing `get_optional_user()` pattern, inadequate secret loading strategy, and endpoint list mismatches — all before a line of code was written. Much cheaper to fix at that stage.

**`asyncio.to_thread()` pattern** — A common trap when using synchronous libraries in FastAPI. `google.oauth2.id_token.verify_oauth2_token()` makes an HTTP request internally. Calling it with no `await` freezes the event loop. Wrap it in `asyncio.to_thread()` to delegate to the thread pool.

**Claude Code `/ship` workflow** — Running type check → API contract sync → code review → security review → auto-commit in one pass noticeably improves commit quality. Automatically verifying that `schemas.py` and `api.ts` changed together was especially useful. The ability to build custom hooks and commands per project is one of Claude Code's real strengths.
