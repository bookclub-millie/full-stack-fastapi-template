# E2E·단위 테스트

어떻게 시험했고 무엇이 확인됐는지 기록한다. 다른 사람이 재현할 수 있도록 시나리오·실행 명령·예상 결과와 실제 결과를 연결한다. 구현 전 시나리오를 작성하고, 시험 후 결과와 근거를 갱신한다.

## 실행 환경과 재현 절차

| 순서 | 재현에 필요한 내용·정확한 명령 |
|---|---|
| 환경 | Python 3.14(`.python-version`), uv(CI는 `latest-known`), Docker Compose v2, Playwright 1.63(Chromium). Bun은 CI마다 다르다: Test Frontend·Playwright 리포트 병합 1.3.12, Frontend Quality 1.4.3(Node 22, `macos-15`), Playwright 컨테이너는 설치 시점의 최신 버전. 그 밖의 CI는 `ubuntu-latest` |
| 합성 데이터·비밀값 없는 설정 | 저장소의 `.env` 개발용 기본값(`FASTAPI_ENV=development`, 관리자 `admin@example.com`). 배포 비밀값은 쓰지 않는다. 테스트 사용자·자료는 테스트가 무작위로 만든다(`backend/tests/utils`, `frontend/tests/e2e/utils`) |
| 설치 | `uv sync --all-packages`, `bun install`(CI는 `bun ci`) |
| 빌드 | `bun run build`(프론트를 `backend/app/frontend`로 빌드), `docker compose build` |
| 기동 | `docker compose up -d --wait db mailpit` → `cd backend && uv run bash scripts/prestart.sh && uv run fastapi dev` → 저장소 루트에서 `bun run dev`. 전체 스택은 `docker compose run --rm backend bash scripts/prestart.sh && docker compose watch` |
| 단위 시험 | 서버: `docker compose up -d --wait db mailpit` 후 `backend`에서 `uv run bash scripts/prestart.sh && uv run bash scripts/tests-start.sh`(테이블은 마이그레이션이 만든다), 커버리지 기준 확인은 `uv run coverage report --fail-under=90`. 프론트: 루트에서 `bun run test:unit` |
| 사용자 흐름 E2E | `docker compose build && docker compose run --rm backend bash scripts/prestart.sh && docker compose run --rm playwright bunx playwright test` |
| 종료 | `docker compose down` |
| 정리 | `docker compose down -v --remove-orphans`(DB 볼륨까지 삭제) |

CI(Test Backend, Frontend Quality, Playwright Tests)도 같은 시험을 돌린다. CI는 여기에 클라이언트 생성, 샤딩, 플래키 실패 처리 같은 단계를 더하므로 정확한 단계는 각 워크플로 파일을 본다. 실행 결과 표에는 [CI 하네스의 시험 결과 수집](ci-harness.md#시험-결과-수집)이 출력한 행만 옮긴다. 환경 준비는 [로컬 개발 안내](local-development.md)를 참고한다. 실행 환경의 정확한 도구 버전과 재현 명령을 기록하고, 비밀값과 실제 개인정보는 기록하지 않는다.

## 테스트 시나리오

| TC | REQ·AC·FLOW | 종류 | 사전 조건 | 입력·행동 | 예상 결과 | 실행 명령 |
|---|---|---|---|---|---|---|

핵심 로직 단위 시험과 사용자 흐름 E2E를 구분한다. TC ID는 테스트 이름에도 붙인다(pytest `test_tc_01_…`, Playwright·vitest `test("TC-01 …")`). 실행 결과는 `backend/tests`(서버 단위·API), `frontend/src/**/*.test.ts`(프론트 단위), `frontend/tests/e2e`(사용자 흐름 E2E)에 있는 이 이름의 테스트에서만 수집한다. 자동화할 수 없는 시험은 종류를 `수동`으로 적는다. 정상·오류·권한 경계·저장 후 재조회를 포함하고, [요구사항](prd.md)과 [사용자 경험](experience.md)의 REQ·AC·FLOW에 연결한다.

### 시나리오 상세 작성 양식

- TC / REQ / AC / FLOW:
- GIVEN — 사용자·권한·데이터·사전 상태:
- WHEN — 호출·입력·사용자 행동:
- THEN — 예상 응답·화면·허용 또는 거부 결과:
- AND — 저장 후 재조회·저장값 불변 등 확인:
- 실행 명령:
- 실제 결과·근거 경로:
- 상태: 미검증

## 실행 결과

| TC | 소스 SHA | 실행 시각·환경 | 실제 결과 | 상태 | 로그·화면 등 근거 경로 |
|---|---|---|---|---|---|

CI 실행 결과를 `python3 scripts/harness/collect_evidence.py --sha <SHA>`로 뽑아 출력된 PASS / FAIL / SKIP 행을 그대로 기록한다. 실행 전은 미검증이며, SKIP·미실행에는 사유를 적는다. HTTP 200이나 테스트 파일의 존재만으로 기능 성공을 판단하지 않는다. 결과는 기록한 소스 SHA·환경·시각에만 해당한다.

## 미검증·실패·제약

| 항목 | 사유·영향 | 후속 확인 방법 |
|---|---|---|
