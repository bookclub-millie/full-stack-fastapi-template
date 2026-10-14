# 로컬 개발 안내

개발 환경을 준비하고 서비스를 띄우는 방법이다. 시험 재현 절차와 도구 버전은 [E2E·단위 테스트](e2e-test.md#실행-환경과-재현-절차)에, CI 검사는 [CI 하네스](ci-harness.md)에 있다. 이 문서는 [개발 과정 기록](development.md)과 다르다.

## 로컬 개발

PostgreSQL과 Mailpit은 Docker Compose로 띄우고, FastAPI와 Vite 개발 서버는 로컬에서 실행한다.

```bash
docker compose up -d --wait db mailpit
```

`backend`에서 의존성을 설치하고 DB를 준비한 뒤(마이그레이션과 첫 관리자 계정), 개발 서버를 띄운다.

```bash
uv sync
uv run bash scripts/prestart.sh
uv run fastapi dev
```

다른 터미널에서 저장소 루트로 가 프론트 의존성을 설치하고 Vite 개발 서버를 띄운다.

```bash
bun install
bun run dev
```

| 주소 | 내용 |
|---|---|
| <http://localhost:5173> | 프론트 개발 서버 |
| <http://localhost:8000> | 백엔드 API |
| <http://localhost:8000/docs> | API 문서(Swagger UI) |
| <http://localhost:8025> | Mailpit(받은 메일 확인) |

프론트 개발 서버는 `frontend/.env`에 설정된 `http://localhost:8000`의 백엔드를 쓴다.

프론트는 Bun 워크스페이스의 Vite·React CSR 앱이다. 공용 디자인 시스템 KDS는 `packages/ui`(`@kds/ui`)에, 메일 템플릿은 `packages/react-email`에 있다. 백엔드 없이 컴포넌트만 개발할 때는 `bun run storybook`을 실행하고 <http://localhost:6006>을 연다. Storybook은 앱 번들에 들어가지 않는다. 로그인이 필요한 화면은 백엔드가 있어야 한다. KDS 사용법은 [프론트 안내](../frontend/README.md)에 있다.

저장소 루트에서 쓰는 검사 명령이다.

| 명령 | 내용 |
|---|---|
| `bun run typecheck` | 프론트와 KDS 타입 검사 |
| `bun run lint:check` | biome 린트·포맷 검사(파일을 고치지 않음) |
| `bun run format` | biome 포맷 적용 |
| `bun run check:deps` | 쓰지 않는 의존성·export 검사(knip) |
| `bun run test:unit` | 프론트 단위 테스트(vitest) |
| `bun run test:storybook` | Storybook 접근성·상호작용 테스트 |
| `bun run build` | 프론트 빌드 |

### FastAPI가 제공하는 프론트 빌드

```bash
bun run build
```

빌드 결과는 `backend/app/frontend`에 써지고, FastAPI가 <http://localhost:8000>에서 제공한다. 프론트를 고친 뒤에는 다시 빌드한다.

## 에이전트 스킬

공용 스킬은 `.agents/skills/`(Codex)에, Claude Code용은 `.claude/skills/`에 있다. 대부분은 `.claude/skills/`에서 `.agents/skills/`로 가는 상대 경로 심링크라 같은 파일을 쓰지만, `openspec-*`와 `library-skills`는 도구가 각 위치에 따로 만든 사본이라 내용이 다를 수 있다.

| 스킬 | 용도 |
|---|---|
| `openspec-*` | OpenSpec 제안·구현·archive 흐름([AGENTS.md](../AGENTS.md)) |
| `impeccable` | UI 디자인 지침·검토 |
| `ux-writing` | 한국어 UI 문구 작성·검수 |
| `vercel-react-best-practices` | React 성능 지침(Next.js·서버 전용 규칙은 해당 코드에만 적용) |
| `fastapi`, `sqlmodel` | 설치된 Python 패키지가 제공하는 스킬(`library-skills`) |

`fastapi`·`sqlmodel` 스킬은 `.venv` 안의 패키지를 가리키는 심링크다. `uv sync`로 백엔드 의존성을 설치하기 전에는 링크가 비어 있다. Impeccable 실행기(`.agents/skills/impeccable/scripts/impeccable`)는 처음 쓸 때 고정된 엔진을 내려받고 체크섬을 확인한다(네트워크 필요, Windows는 `impeccable.cmd`).

## Docker Compose 전체 스택

백엔드와 빌드된 프론트를 Docker Compose로 띄운다.

```bash
docker compose run --rm backend bash scripts/prestart.sh
docker compose watch
```

| 주소 | 내용 |
|---|---|
| <http://localhost:8000> | FastAPI가 제공하는 앱과 API |
| <http://localhost:8000/docs> | API 문서(Swagger UI) |
| <http://localhost:8080> | Adminer(DB 관리) |
| <http://localhost:8090> | Traefik UI(라우팅 확인) |
| <http://localhost:8025> | Mailpit |

로컬에서 띄운 FastAPI 서버가 있으면 먼저 멈춘다. 두 서버가 같은 8000 포트를 쓴다. 처음 띄울 때는 모든 서비스가 준비되기까지 1분쯤 걸릴 수 있다. `docker compose logs`(백엔드만은 `docker compose logs backend`)로 상태를 본다.

## Mailpit

[Mailpit](https://mailpit.axllent.org)은 로컬 개발 중 보내는 메일을 실제로 보내지 않고 받아 둔다. 로컬 백엔드는 `localhost:1025`, Compose 백엔드는 `mailpit` 서비스로 연결한다. 받은 메일은 <http://localhost:8025>에서 본다.

## Docker Compose 파일과 환경변수

- `compose.yml`: 전체 스택이 공유하는 설정. Docker Compose가 자동으로 읽는다.
- `compose.override.yml`: 소스 마운트 같은 로컬 개발 설정. 자동으로 읽혀 `compose.yml` 위에 덧씌워진다.
- `compose.deploy.yml`: HTTPS와 인증서 자동 발급 같은 배포 설정. 배포할 때 `compose.yml`과 함께 명시해 쓴다.

백엔드는 `.env`에서 설정을 읽는다. Docker Compose도 이 파일로 변수를 채우고 컨테이너마다 필요한 값을 넘긴다. 변수를 바꾸면 `docker compose watch`로 다시 띄운다.

## `.env` 파일

저장소에 있는 `.env`는 로컬 개발용 기본값(비밀번호 포함)이다. 호스트 이름은 로컬 프로세스 기준 `localhost`이고, Docker Compose가 DB·SMTP 같은 호스트를 서비스 이름으로 바꾼다. 배포용 비밀값은 `.env`에 넣지 말고 [FastAPI Cloud 배포](../deployment.md)나 [Docker Compose 배포](../deployment-docker-compose.md) 안내대로 설정한다.

## pre-commit 훅과 린트

린트와 포맷은 [prek](https://prek.j178.dev/)(pre-commit 대체 도구)으로 실행한다. 설정은 저장소 루트의 `.pre-commit-config.yaml`이고, prek은 이미 프로젝트 의존성에 들어 있다.

커밋할 때마다 자동으로 실행되도록 훅을 설치한다(`-f`는 기존 pre-commit 훅을 덮어쓴다).

```bash
uv run prek install -f
```

이후 `git commit`을 하면 커밋할 파일을 검사·포맷한다. prek이 파일을 고쳤으면 다시 `git add`한 뒤 커밋한다. 모든 파일을 직접 검사할 때는 다음을 실행한다.

```bash
uv run prek run --all-files
```
