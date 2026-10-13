# 아키텍처

서비스를 어떻게 구성했는지 기록한다. 설계 시 선택 이유를 적고, 구현·배포 후 코드와 실제 데이터 흐름에 맞춰 갱신한다.

## 스택과 선택 이유

| 영역 | 기술·버전 | 선택 이유 | 소스·설정 위치 |
|---|---|---|---|
| Backend | Python 3.14, FastAPI 0.141, SQLModel 0.0.47, Pydantic 2.13, Alembic 1.20 | 타입으로 API 검증·문서(OpenAPI)·ORM 모델을 함께 정의 | `backend/app`, `backend/pyproject.toml` |
| DB | PostgreSQL 18, psycopg 3.3 | 관계형 데이터와 트랜잭션. Docker로 로컬·CI·배포 환경을 맞춤 | `compose.yml`, `backend/app/alembic` |
| Frontend | React 19, TypeScript 6, Vite 8, TanStack Router·Query | CSR 앱, 파일 기반 라우팅, 서버 상태 캐시 | `frontend/src` |
| UI | KDS(`@kds/ui`), Tailwind CSS 4, Storybook | 팀 디자인 시스템의 공용 컴포넌트와 토큰 | `packages/ui`, `frontend/.storybook` |
| API 클라이언트 | OpenAPI에서 자동 생성한 TypeScript 클라이언트 | 백엔드 모델과 프론트 타입을 일치시킴 | `frontend/src/client`, `scripts/generate-client.sh` |
| 인증 | JWT(HS256, PyJWT), Argon2 비밀번호 해시(pwdlib) | OAuth2 비밀번호 흐름 표준 구현 | `backend/app/core/security.py`, `backend/app/api/deps.py` |
| 테스트 | pytest, vitest 4, Playwright 1.63 | 서버 단위·API, 프론트 단위, 사용자 흐름 E2E | `backend/tests`, `frontend/src/**/*.test.ts`, `frontend/tests/e2e` |
| 실행·배포 | Docker Compose, Traefik 3.7(HTTPS), FastAPI Cloud 워크플로(선택) | 로컬과 배포 구성을 같은 파일로 관리 | `compose*.yml`, `deployment.md`, `deployment-docker-compose.md` |
| CI | GitHub Actions + 하네스(비밀값·공급망·워크플로·추적성 검사) | 사람과 AI 에이전트의 변경을 같은 기준으로 검사 | `.github/workflows`, [CI 하네스](ci-harness.md) |

위 행은 템플릿의 기본 구성이다. 주제 기능에서 외부 서비스·저장소·라이브러리를 더하면 행을 추가하고 선택 이유를 적는다.

## 구성과 데이터 흐름

템플릿 기준 흐름이다. 주제 기능의 흐름은 아래에 이어서 적는다.

1. 브라우저의 React 앱이 OpenAPI 생성 클라이언트(`frontend/src/client`)로 `/api/v1/*`를 호출한다.
2. FastAPI 라우터(`backend/app/api/routes`)가 요청 본문을 Pydantic·SQLModel 모델(`backend/app/models.py`)로 검증한다.
3. 의존성(`backend/app/api/deps.py`)이 DB 세션과 현재 사용자를 넣고, CRUD(`backend/app/crud.py`)가 SQLModel로 PostgreSQL을 읽고 쓴다.
4. 응답은 공개용 모델(예: `UserPublic`)로 직렬화한다. 배포 빌드에서는 프론트 정적 파일도 FastAPI가 제공한다(`backend/app/frontend`).

## 데이터·API·권한 경계

- 인증: `POST /api/v1/login/access-token`이 JWT를 발급하고, 이후 요청은 `Authorization: Bearer` 헤더로 보낸다.
- 인가: 로그인이 필요한 API는 `CurrentUser`, 관리자 API는 `get_current_active_superuser`를 쓴다. 자료 소유권은 라우트에서 확인한다(예: items의 `owner_id`).
- 개발 전용 API(`backend/app/api/routes/private.py`)는 `FASTAPI_ENV=development`일 때만 등록된다.
- CORS는 `FRONTEND_HOST` 한 곳만 허용한다(`backend/app/main.py`).
- mock: 로컬·CI에서 메일은 실제로 보내지 않고 Mailpit이 받는다.

## 의존성·배포·복구

- 외부 의존성: PostgreSQL, SMTP(로컬은 Mailpit).
- 기동 전 `backend/scripts/prestart.sh`가 마이그레이션을 적용하고(`alembic upgrade head`) 첫 관리자 계정을 만든다(`app/initial_data.py`). DB가 먼저 떠 있어야 한다(`docker compose up -d --wait db`).
- 배포: Docker Compose(Traefik이 HTTP를 HTTPS로 전환, [안내](../deployment-docker-compose.md)) 또는 FastAPI Cloud(저장소 변수 `FASTAPI_CLOUD_DEPLOY=true`일 때만 실행, [안내](../deployment.md)).
- 복구: 로컬은 `docker compose down -v` 후 `prestart.sh`로 다시 만든다(데이터가 지워진다). 운영 데이터 백업은 템플릿에 없다.

## 주요 결정

| ADR | 결정 | 상태 |
|---|---|---|
| [ADR-001](adr/001-openspec-docs-traceability.md) | OpenSpec과 문서·Issue를 ID로 연동 | 채택 |

저장소 전반에 영향을 주는 결정은 [ADR 템플릿](adr/000-template.md)을 복사해 기록한다.
