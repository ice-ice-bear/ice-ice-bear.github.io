---
image: "/images/posts/2026-03-17-hybrid-search-auth/cover.jpg"
title: "하이브리드 이미지 검색 개발기 — Google OAuth 로그인 월 구현"
description: "FastAPI와 React에 Google OAuth 로그인을 구현하고 JWT 쿠키 기반 인증으로 전체 API를 보호하는 과정"
date: 2026-03-17
categories: ["dev-log"]
tags: ["hybrid-search", "google-oauth", "jwt", "fastapi", "react", "python"]
toc: true
math: false
---

## 개요

하이브리드 이미지 검색 데모 앱에 Google OAuth 로그인을 추가했다. 기존에는 인증이 전혀 없어서 모든 API 엔드포인트가 완전히 열려 있었는데, 특히 Gemini API를 호출하는 이미지 생성 기능이 비용을 발생시키기 때문에 인증 없이 방치할 수 없었다. 이번 작업에서는 설계 문서 작성부터 스펙 리뷰, 구현 계획, 실제 코딩, 보안 리뷰까지 전 과정을 Claude Code의 superpowers 플러그인 워크플로우로 진행했다. 총 17개의 커밋으로 완전한 로그인 월(login wall)을 구현했다.

<!--more-->

## 인증 아키텍처

로그인 방식으로 **Lightweight Custom Auth**를 선택했다. FastAPI-Users 같은 라이브러리는 비밀번호 리셋, 이메일 인증 등 불필요한 기능이 15개 이상 딸려 오고, Authlib + Session Middleware는 서버 사이드 리다이렉트 방식이라 SPA 구조와 맞지 않았다. 직접 구현하면 코드 전체를 이해하고 디버깅할 수 있다는 장점이 있다.

핵심 스택:
- **Backend**: `google-auth` (Google ID 토큰 검증) + `python-jose` (JWT 생성/검증)
- **Frontend**: `@react-oauth/google` (Google Sign-In 팝업 버튼)
- **세션**: HttpOnly 쿠키에 JWT 저장 (localStorage 방식보다 XSS에 안전)

### 인증 플로우

```mermaid
sequenceDiagram
    participant U as User
    participant F as React Frontend
    participant G as Google OAuth
    participant B as FastAPI Backend
    participant DB as SQLite

    U->>F: 앱 접속
    F->>B: GET /api/auth/me
    B-->>F: 401 Unauthorized
    F->>U: LoginPage 표시

    U->>F: Google Sign-In 클릭
    F->>G: OAuth 팝업
    G-->>F: ID Token 반환

    F->>B: POST /api/auth/google&lt;br/&gt;{id_token}
    B->>G: verify_oauth2_token()
    G-->>B: Claims (sub, email, name, picture)
    B->>DB: get_or_create_user()
    DB-->>B: User 객체
    B->>B: create_jwt(user_id)
    B-->>F: Set-Cookie: access_token=JWT&lt;br/&gt;(HttpOnly, SameSite=Lax)
    B-->>F: LoginResponse {user}

    F->>U: 메인 앱 전환

    Note over F,B: 이후 모든 요청

    F->>B: API 요청&lt;br/&gt;(쿠키 자동 첨부)
    B->>B: get_current_user()&lt;br/&gt;JWT 검증
    B-->>F: Protected 데이터
```

## 데이터베이스 변경

### User 모델 추가

기존에 `SearchLog`, `ImageSelection`, `GenerationLog`, `ManualUpload` 4개 테이블이 있었고, 모두 사용자 개념 없이 익명으로 기록되고 있었다. 새로 `User` 테이블을 만들고, 기존 4개 테이블에 `user_id` FK 컬럼을 추가했다.

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

기존 데이터는 건드리지 않기로 했다. FK 컬럼은 `nullable=True`로 선언해서 기존 행은 `user_id=NULL`로 남기고, 새로운 행만 인증 미들웨어에서 `user_id`를 채운다. Alembic 마이그레이션 1개로 테이블 생성과 FK 추가를 처리했다.

## Backend 구현

### auth.py — 인증 모듈

모든 인증 로직을 `backend/src/auth.py` 하나에 모았다. 세 가지 핵심 함수가 있다.

**1. Google 토큰 검증** — `verify_google_token()`

```python
async def verify_google_token(token: str) -> dict:
    try:
        # verify_oauth2_token은 동기 함수이고 Google 공개키를 네트워크로 가져올 수 있음
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

보안 리뷰에서 `asyncio.to_thread()`로 감싸는 수정이 들어갔다. `verify_oauth2_token()`은 동기 함수인데 Google의 공개키를 네트워크에서 가져오는 I/O가 발생할 수 있어서, 그냥 호출하면 이벤트 루프를 블로킹한다.

**2. JWT 쿠키 관리** — `create_jwt()` / `set_auth_cookie()`

JWT에는 `user_id`와 `exp`만 담는다. 쿠키 설정에서 중요한 부분:
- `HttpOnly` — JavaScript에서 토큰을 읽을 수 없어 XSS 방지
- `SameSite=Lax` — CSRF 보호 (추가 CSRF 토큰 불필요)
- `Secure` — 프로덕션(HTTPS)에서만 활성화, 로컬 개발은 비활성화

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

    # last_active_at 업데이트 (분당 1회 throttling)
    now = datetime.now(timezone.utc)
    if not user.last_active_at or (now - user.last_active_at).seconds > 60:
        await update_last_active(user.id)

    return user
```

`last_active_at` 업데이트를 매 요청마다 하면 SQLite에 쓰기 부하가 걸리므로, 분당 1회로 throttling한다. 또한 `/api/auth/me`용으로 401 대신 `None`을 반환하는 `get_optional_user()` 변형도 만들었다.

### 엔드포인트 보호

기존 10개 데이터 접근 엔드포인트 전부에 `user = Depends(get_current_user)`를 추가했다. 이미지 생성 엔드포인트에서는 추가로 `increment_generation_count(user.id)`를 호출한다. 모든 로그 함수(`log_search`, `log_image_selection` 등)에 `user_id` 파라미터를 추가하고, 서비스 레이어에서 해당 컬럼에 저장한다.

```
# 보호 대상 (get_current_user 필수)
POST /search, /search/simple, /search/hybrid, GET /search
POST /api/generate-image, /api/log-selection, /api/upload-reference-image
GET /api/history/generations, /api/images, /api/images/{image_id}

# 비보호 (인증 불필요)
GET /, /health, /api/info, /images/{filename}
POST /api/auth/google, /api/auth/logout
GET /api/auth/me
```

## Frontend 로그인 플로우

### LoginPage 컴포넌트

`@react-oauth/google`의 `<GoogleLogin>` 컴포넌트로 팝업 방식의 로그인을 구현했다. 리다이렉트 방식이 아니라 팝업에서 Google 계정을 선택하면 바로 ID 토큰이 콜백으로 돌아온다.

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

### App.tsx 변경

앱 진입점에서 인증 상태를 관리한다:

1. **마운트 시** — `GET /api/auth/me` 호출. 성공하면 기존 세션 복구, 401이면 로그인 페이지 표시
2. **조건부 렌더링** — `authLoading` → 스피너, `!user` → `<LoginPage>`, else → 기존 UI
3. **로그아웃** — 우측 상단 버튼, `POST /api/auth/logout` 호출 후 상태 초기화
4. **데이터 로딩 가드** — `useEffect`에서 `if (!user) return;`으로 로그인 전 API 호출 방지

```tsx
// App.tsx (핵심 로직)
useEffect(() => {
  if (!user) return;
  const loadHistory = async () => {
    const items = await fetchGenerationHistory(20, 0);
    setGeneratedImages(mapHistoryItems(items));
  };
  loadHistory();
}, [user]);
```

### api.ts — Axios 설정

```typescript
// withCredentials: true — 브라우저가 쿠키를 자동으로 요청에 첨부
const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
});

// 401 인터셉터 — 토큰 만료 시 자동으로 로그인 페이지로 전환
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

## 보안 리뷰

구현 후 `/ship` 커맨드로 보안 리뷰를 실행했다. 발견된 주요 사항과 수정 내용:

| 항목 | 문제 | 수정 |
|------|------|------|
| Google 토큰 검증 | 동기 함수가 이벤트 루프 블로킹 | `asyncio.to_thread()`로 감싸기 |
| JWT 시크릿 미설정 | 시크릿 없이 서버 시작 시 모든 인증 실패 | `configure_auth()`에서 `logger.warning` 출력 |
| `create_jwt()` 가드 | `JWT_SECRET=None`일 때 서명 시도 | `RuntimeError` 발생시키도록 가드 추가 |
| 프론트엔드 스타일 | 하드코딩된 inline style | Tailwind CSS 클래스로 전환 |
| 히스토리 로딩 | 로그인 전 API 호출 시도 | `user` 의존성 가드 추가 |

시크릿 관리도 설계 시 고려했다. `GOOGLE_OAUTH_CLIENT_ID`와 `JWT_SECRET`은 yaml 설정 파일이 아닌 `os.getenv()`로 로드한다. yaml은 버전 관리 대상이므로 시크릿을 넣으면 안 된다. 토큰 만료 시간 같은 비밀이 아닌 설정만 `config.py`의 `AuthConfig`에 담는다.

## 개발 도구: /ship 커맨드와 PostToolUse 훅

이번 작업에서는 프로젝트 전용 개발 도구도 함께 세팅했다.

**PostToolUse 훅** — 파일 수정할 때마다 자동으로 타입 체크:
- `.ts/.tsx` 파일 수정 → `tsc --noEmit` 자동 실행
- `backend/*.py` 파일 수정 → `pyright` 자동 실행

**`/ship` 커맨드** — 커밋 전 6단계 검증 파이프라인:
1. 변경 파일 식별
2. 타입 검증 (tsc + pyright)
3. API contract 동기화 확인 (`schemas.py` ↔ `api.ts`)
4. 코드 단순화 리뷰
5. 보안 리뷰
6. 자동 커밋

한 가지 재미있는 삽질이 있었는데, PostToolUse 훅에서 `$CLAUDE_FILE_PATH` 환경변수를 사용했더니 동작하지 않았다. 알고 보니 훅은 **stdin JSON**으로 입력을 받는 구조였다:
```bash
INPUT=$(cat)
FILEPATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
```

## 커밋 로그

| 커밋 | 메시지 | 주요 파일 |
|------|--------|----------|
| `f19c331d` | docs: Google 로그인 설계 스펙 | `2026-03-17-google-login-design.md` |
| `b8993da9` | docs: 스펙 리뷰 피드백 반영 | 동일 |
| `34b67262` | docs: 엔드포인트 경로 및 설명 일관성 수정 | 동일 |
| `734048ec` | docs: 구현 계획서 작성 | `2026-03-17-google-login.md` |
| `840c0e8a` | feat: User 모델 + user_id FK 추가 | `models.py`, Alembic 마이그레이션 |
| `1eb6e9b0` | feat: google-auth, python-jose 의존성 | `requirements.txt` |
| `e2502dc4` | feat: @react-oauth/google 의존성 | `package.json` |
| `a2de355f` | feat: 인증 Pydantic 스키마 | `schemas.py` |
| `9bc52d0d` | feat: 사용자 CRUD 및 활동 추적 | `service.py` |
| `c80d6de7` | feat: auth 모듈 (토큰 검증 + JWT 쿠키) | `auth.py` |
| `c039091c` | feat: AuthConfig 추가 | `config.py`, `default.yaml` |
| `57ce55f6` | feat: LoginPage 컴포넌트 | `LoginPage.tsx` |
| `ff989bd7` | feat: auth API 함수, 401 인터셉터 | `api.ts` |
| `cd9d25bd` | feat: 인증 상태, 로그인/로그아웃 플로우 | `App.tsx` |
| `128be9bb` | feat: auth 엔드포인트 + 전체 라우트 보호 | `main.py`, `service.py` |
| `395fa5b9` | fix: 보안 가드, async 토큰 검증, UI | `auth.py`, `App.tsx` |
| `8ccefefd` | feat: Google OAuth 로그인 월 완성 | 최종 병합 |

## 인사이트

**HttpOnly 쿠키 vs localStorage** — SPA에서 JWT를 localStorage에 넣는 튜토리얼이 많지만, XSS 한 방이면 토큰이 털린다. HttpOnly 쿠키는 JavaScript가 아예 접근할 수 없어서, 특히 Gemini API처럼 과금이 되는 서비스를 보호할 때는 이쪽이 맞다. 구현 복잡도 차이는 CORS에 `allow_credentials=True` 추가하는 정도밖에 없다.

**설계 먼저, 코드는 나중에** — 이번에 설계 스펙 → 리뷰 → 구현 계획 → 리뷰 → 코딩 순서로 진행했다. 시간이 더 걸리는 것 같지만, 스펙 리뷰에서 `get_optional_user()` 패턴 누락, 시크릿 로딩 전략 미비, 엔드포인트 목록 불일치 등을 코딩 전에 잡았다. 코드 리뷰에서 잡는 것보다 수정 비용이 훨씬 적다.

**`asyncio.to_thread()` 패턴** — FastAPI에서 동기 라이브러리를 쓸 때 흔히 빠지는 함정이다. `google.oauth2.id_token.verify_oauth2_token()`은 내부에서 HTTP 요청을 보내는데, `await` 없이 호출하면 이벤트 루프가 멈춘다. `asyncio.to_thread()`로 스레드 풀에 위임하는 패턴을 기억해두자.

**Claude Code `/ship` 워크플로우** — 타입 체크 → API contract 동기화 → 코드 리뷰 → 보안 리뷰 → 자동 커밋을 한 번에 돌리니, 커밋 품질이 확실히 올라간다. 특히 `schemas.py`와 `api.ts`가 동시에 바뀌었는지 자동으로 확인해주는 부분이 유용했다. 프로젝트별로 커스텀 훅과 커맨드를 만들 수 있다는 점이 Claude Code의 강점이다.
