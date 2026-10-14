# 프론트엔드

React와 TypeScript로 구성한 클라이언트 렌더링(CSR) 웹 앱입니다. Vite로 개발·빌드하고, TanStack Router로 페이지 이동을, TanStack Query로 서버 데이터를 관리합니다. UI는 Tailwind CSS와 공유 KDS 패키지 `@kds/ui`를 사용합니다.

`frontend`와 `packages/*`는 Bun 워크스페이스로 연결되어 있습니다. 의존성 설치와 아래 명령은 별도 안내가 없으면 **저장소 루트**에서 실행합니다.

## 시작하기

개발 도구 기준은 Node.js 22와 Bun 1.4.3입니다.

```bash
bun install
bun run dev
```

개발 서버: <http://localhost:5173>

로그인과 데이터 조회에는 백엔드와 PostgreSQL이 필요합니다. 설정·기동 방법은 [전체 개발 환경 안내](../docs/local-development.md)를 참고합니다. 컴포넌트만 개발할 때는 백엔드 없이 Storybook을 사용할 수 있습니다.

### API 연결

`frontend/.env`에서 API 주소를 설정합니다.

```dotenv
VITE_API_URL=http://localhost:8000
```

- 주소를 비우면 현재 페이지와 같은 출처로 요청합니다.
- 원격 API는 절대 HTTP(S) 주소를 사용합니다. 사용자 정보·쿼리·해시가 포함된 주소는 허용하지 않습니다.
- `VITE_*` 값은 브라우저에 공개되는 빌드 시점 설정입니다. 토큰·비밀번호·서버 비밀값을 넣지 않습니다.
- 값을 변경하면 개발 서버를 다시 시작합니다.

TanStack 개발 도구는 기본적으로 숨겨져 있습니다. 필요할 때만 `VITE_ENABLE_DEVTOOLS=true bun run dev`로 켭니다. 프로덕션에서는 비활성화됩니다.

## 폴더 구조

```text
frontend/
├── .storybook/          # Storybook 설정
├── public/              # 이미지·폰트 라이선스 등 정적 파일
├── src/
│   ├── client/          # OpenAPI로 생성한 API 클라이언트
│   ├── components/      # 화면 구성 요소와 공통 컴포넌트
│   ├── hooks/           # 공통 훅
│   ├── lib/             # 환경 설정·공통 유틸리티
│   ├── routes/          # 페이지와 라우팅
│   ├── stories/         # 컴포넌트 사용 예시
│   └── index.css        # 전역 스타일
├── tests/
│   └── e2e/            # 백엔드와 연결한 서비스 기능 검증
└── design.md            # 공통 디자인 원칙

packages/
├── ui/                  # 공유 KDS 컴포넌트
└── react-email/         # 이메일 템플릿
```

## 화면과 컴포넌트 개발

공통 시각·상호작용 원칙은 [디자인 가이드](design.md)를 따릅니다. 기본 테마는 라이트이며, 화면 문구는 한글로 작성합니다. 입력 안내와 오류 메시지는 사용자가 다음에 할 행동을 알 수 있게 씁니다.

KDS 컴포넌트는 필요한 경로에서 가져옵니다.

```tsx
import { Button } from '@kds/ui/components/button'

export const SaveAction = () => <Button>저장</Button>
```

`src/index.css`에서 공유 스타일 `@kds/ui/globals.css`를 불러옵니다. KDS는 Base UI 기반이며, 기존 `src/components/ui`의 Radix 기반 컴포넌트와 조합 방식이 다를 수 있습니다. Tooltip을 사용할 때는 상위에 `TooltipProvider`를 둡니다.

### Storybook

```bash
bun run storybook
```

Storybook: <http://localhost:6006> · 사용 예시: `src/stories`

## 코드 작성 규칙

- 함수는 `const` 함수 표현식과 화살표 함수를 우선합니다. 동적 `this`가 필요하면 일반 함수 표현식을 사용합니다.
- 파일명과 폴더명은 `auth-layout.tsx`, `use-auth.ts`, `user-settings/`처럼 소문자 케밥케이스로 작성합니다. 컴포넌트 이름은 PascalCase, 훅 이름은 camelCase를 사용합니다.
- `__root.tsx`, `_layout.tsx`, `*.stories.tsx`, `*.spec.ts` 등 도구가 사용하는 파일 규칙은 유지합니다.
- 페이지 컴포넌트를 참조하는 라우트 정의는 컴포넌트 뒤에 둡니다.
- `src/client`와 `routeTree.gen.ts` 같은 생성 코드는 직접 수정하지 않습니다.

포맷은 루트 [biome.json](../biome.json)으로 통일합니다. **2칸 들여쓰기·작은따옴표·후행 쉼표 없음·필요한 경우에만 세미콜론**을 사용하는 StandardJS 계열 스타일입니다. JSX 속성은 큰따옴표를 사용하며, StandardJS 린트 규칙 전체를 강제하지는 않습니다.

```bash
bun run format
```

포맷과 import 정리만 적용합니다.

## 빌드와 API 클라이언트

### 서비스 빌드

```bash
VITE_API_URL="" bun run build
```

같은 출처의 API를 사용하는 배포용 빌드입니다. 결과는 `backend/app/frontend`에 생성되며 FastAPI에서 제공합니다. 원격 API를 사용할 때는 빈 값 대신 해당 주소를 지정합니다. 빌드에는 프론트엔드 타입 검사가 포함됩니다.

Docker 빌드에서도 `@kds/ui`를 찾을 수 있도록 저장소 루트와 `packages`를 빌드 컨텍스트에 포함해야 합니다.

### API 클라이언트 갱신

백엔드의 OpenAPI 스키마가 바뀌면 다음 명령으로 갱신합니다. 백엔드 개발 환경이 준비되어 있어야 합니다.

```bash
bash scripts/generate-client.sh
```

생성 결과: `src/client`

## 검사와 테스트

| 명령 | 용도 |
| --- | --- |
| `bun run format:check` | 파일을 바꾸지 않고 포맷·import 정리 상태 확인 |
| `bun run lint` | 설정된 린트 규칙 검사 |
| `bun run lint:check` | 포맷·import·린트 규칙 함께 검사 |
| `bun run typecheck` | 프론트엔드와 공유 UI 타입 검사 |
| `bun run check:deps` | 미사용 파일·의존성 분석 |
| `bun run test:unit` | 단위 테스트와 지정된 파일의 커버리지 측정 |
| `bun run test:storybook` | 컴포넌트 상호작용·접근성 검사 |
| `bun run test` | 백엔드와 연결한 E2E 테스트 |

브라우저 테스트는 `frontend`에서 `bunx playwright install chromium`으로 브라우저를 준비합니다. E2E는 백엔드·DB 등 [개발 환경](../docs/local-development.md)이 필요합니다.

### 생성 결과물

`storybook-static`, `test-results`, `playwright-report`, `blob-report`, `coverage`는 Git에서 제외되는 빌드·테스트 결과물로, 삭제해도 됩니다.

## 관련 문서와 출처

- [공통 디자인 가이드](design.md)
- [전체 개발 환경](../docs/local-development.md)
- [프로젝트 문서](../docs/README.md)
- 프로젝트 기반: [FastAPI Full Stack Template](https://github.com/fastapi/full-stack-fastapi-template)
- 프론트엔드 도구 구성 참고: [Next.js Boilerplate](https://github.com/ixartz/Next-js-Boilerplate)
- 일러스트: [Open Doodles](https://www.opendoodles.com/) · Pablo Stanley · [CC0](https://creativecommons.org/publicdomain/zero/1.0/)
- 글꼴 라이선스: [Pretendard SIL Open Font License](public/fonts/Pretendard-LICENSE.txt)
- 프로젝트 라이선스: [LICENSE](../LICENSE)
