# 프로젝트 이름

<!-- 해커톤 주제가 정해지면 서비스 이름과 한두 문장 소개로 바꾼다. 자세한 내용은 docs/project-brief.md에 쓴다. -->

## 빠른 시작

필요한 도구: Docker Compose v2, Python 3.14와 uv, Bun. 정확한 버전은 [시험 환경](./docs/e2e-test.md#실행-환경과-재현-절차)에 있다.

```bash
docker compose up -d --wait db mailpit
(cd backend && uv sync && uv run bash scripts/prestart.sh && uv run fastapi dev)
# 다른 터미널, 저장소 루트에서
bun install && bun run dev
```

<http://localhost:5173>에서 앱을, <http://localhost:8000/docs>에서 API 문서를 연다. 로그인 계정은 `.env`의 `FIRST_SUPERUSER`다(개발용 값). 자세한 내용은 [로컬 개발 안내](./docs/local-development.md)에 있다.

## 실행 및 검증

다른 개발자가 같은 환경에서 설치·실행·시험을 재현할 수 있도록 정확한 버전·의존성·비밀값 없는 설정과 명령을 기록한다. 새 환경에서 확인한 결과와 미검증·제약을 구분한다.

| 단계 | 안내 |
|---|---|
| 환경·버전·의존성·설정 | [로컬 개발](./docs/local-development.md#로컬-개발), [시험 환경](./docs/e2e-test.md#실행-환경과-재현-절차) |
| 설치·빌드·기동 | [로컬 개발](./docs/local-development.md#로컬-개발), [프론트 빌드](./docs/local-development.md#fastapi가-제공하는-프론트-빌드), [전체 스택](./docs/local-development.md#docker-compose-전체-스택) |
| 시험·종료·정리 | [테스트 재현 절차](./docs/e2e-test.md#실행-환경과-재현-절차) |
| 실제 시험 SHA·시각·결과 위치 | [실행 결과](./docs/e2e-test.md#실행-결과) |
| 미검증·실패·제약 | [검증 제약](./docs/e2e-test.md#미검증실패제약) |

서비스 개요·요구사항·설계·개발·보안·테스트 문서는 [문서 안내](./docs/README.md)를 참고한다.
