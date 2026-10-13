# ADR-001: OpenSpec과 문서·Issue 연동

- 상태: 채택
- 날짜: 2026-10-14
- 관련 REQ·Issue·PR: #1(CI 하네스), #3(OpenSpec 설정), #4·#5·#6(구현), #10(TC 이름 검사), vitest 수집 추가(2026-10-14)

## 맥락

- 기술평가는 문서·코드·실제 실행과 테스트 결과·GitHub 이력·AI 활용 기록을 함께 본다. 문서는 **요구(REQ) → 확인 조건(AC) → Issue·코드 → 시험(TC) → 실제 결과**를 연결해야 하고, 예시·계획·미검증을 완료로 쓰면 안 된다([온보딩 안내](https://aidx-onboarding.koreacentral.cloudapp.azure.com/#documents)).
- Issue는 개발 작업·검증 양식(`[REQ-01] 제목`, 목적, 완료 조건, 담당자 / 연결 문서, 구현·검증 근거)으로 등록한다. 근거를 연결한 뒤 **Close as completed**로 닫아야 완료로 집계되고, 취소·중복은 **Close as not planned**로 닫는다([안내](https://aidx-onboarding.koreacentral.cloudapp.azure.com/#issues)).
- 기능은 OpenSpec(`openspec/`)으로 제안 → 구현 → archive한다. OpenSpec 산출물(proposal·spec의 Requirement와 Scenario·design·tasks)은 위 고리의 앞부분을 이미 구조화된 형태로 담는다. 다만 OpenSpec의 Requirement에는 REQ·AC 같은 ID가 없다.
- master는 ruleset으로 직접 push가 막혀 있다. CI가 master의 문서를 직접 고칠 수 없다.

## 결정

OpenSpec을 작업 단위의 원천으로 두고, 문서(`docs/*.md`, `README.md`)는 평가자가 읽는 기록으로 둔다. 둘은 **ID**로 연결한다. 문서 본문은 PR 안에서 사람과 에이전트가 갱신한다. CI는 문서를 쓰지 않고 **검사**와 **실제 데이터 제공**만 맡는다.

### 1. ID 규칙 (`openspec/config.yaml`)

| OpenSpec 위치 | 규칙 | 연결되는 문서 |
|---|---|---|
| proposal.md 첫 줄 | `# <기능 이름>` | Issue 제목 |
| proposal.md 머리 | `요구사항: REQ-01[, REQ-02]`, `담당: @github-id`, `범위: 필수 \| 추가` | `prd.md` 추적표, `project-brief.md` 범위, Issue 담당자 |
| spec의 Requirement | `### Requirement: REQ-01 <이름>` | `prd.md` REQ |
| spec의 Scenario | `#### Scenario: AC-01 <이름>`. 사용자 흐름·보안 항목이면 본문에 `연결: FLOW-01, SEC-03` | `prd.md` AC, `experience.md` FLOW, `security-compliance.md` SEC |
| 테스트 이름 | pytest `test_tc_01_...`(`backend/tests`), Playwright `test("TC-01 ...")`(`frontend/tests/e2e`), vitest `it("TC-01 ...")`(`frontend/src/**/*.test.ts`). 테스트 하나에 TC 하나. `TC-1`과 `TC-01`은 같은 TC | `e2e-test.md` TC와 실행 결과 |
| tasks.md 테스트 작업 | `- [ ] 2.3 TC-07 (AC-07) <파일>::<테스트 이름>`. 파일 위치는 spec PR에서 리뷰한다 | 구현할 테스트, archive 때 실제 위치와 대조 |

REQ·AC·FLOW·TC 번호는 저장소 전체에서 하나씩 증가시킨다. 새 번호는 `prd.md`·`experience.md`·`e2e-test.md`에 있는 가장 큰 번호 다음을 쓴다.

### 2. 단계별 문서 갱신 (`openspec/config.yaml` 규칙·지침, `AGENTS.md`)

| 단계 | 할 일 |
|---|---|
| propose | tasks.md의 마지막 그룹을 **문서·근거**로 둔다: `prd.md` 추적표 행(상태 `계획`), `experience.md` FLOW, 해당하면 `security-compliance.md` SEC 행, 저장소 전체 결정이면 ADR. TC 테스트 작업 줄은 구현 그룹 안에 두고, 같은 줄에서 `e2e-test.md` 시나리오 행을 함께 추가한다. |
| apply | tasks.md에 적힌 파일·이름 그대로 TC ID를 단 테스트를 작성한다. 문서·근거 그룹 작업을 수행한다. 마치기 전에 `scripts/harness/tc_check.py`를 통과시킨다. |
| archive | 증거 수집 도구(5번)의 출력으로 `e2e-test.md` 실행 결과를 채운다. `prd.md`·`experience.md`·`security-compliance.md` 상태를 실제 결과로 바꾼다. `development.md` "AI 활용과 검증"에 이 변경의 행을 추가한다. |

`AGENTS.md`에는 "기능·동작 변경은 OpenSpec으로 시작한다, Issue는 손으로 만들거나 닫지 않는다, 결과는 증거 수집 도구의 출력만 옮긴다" 수준의 짧은 규칙만 둔다. 형식 규칙은 `openspec/config.yaml` 한 곳에만 둔다.

### 3. Issue 동기화 (`.github/workflows/openspec-issues.yml`)

- 실행: master push(`openspec/**`), 수동 실행, 매시간. master의 코드만 실행한다. 권한은 `issues: write`, `contents·pull-requests·checks: read`.
- 구성: Python(표준 라이브러리, 토큰 없음)이 OpenSpec을 읽어 변경별 원하는 Issue 상태를 JSON으로 만든다. github-script가 실제 Issue와 대조해 반영한다.
- 대응: 변경 1개 = Issue 1개.

  | Issue | 출처 |
  |---|---|
  | 제목 `[REQ-01] 기능 이름` | proposal의 `요구사항`과 첫 줄. REQ가 없으면 `[OpenSpec] 기능 이름` |
  | 목적 | proposal의 Why |
  | 완료 조건 | Scenario마다 `- [ ] AC-01 <이름>` + `- [ ] 정상·오류 테스트 결과를 남긴다` |
  | 담당자 / 연결 문서 | `담당`(Assignee 지정, 없으면 PR 작성자), `docs/prd.md`의 REQ, OpenSpec 경로 |
  | 구현·검증 근거 | archive 때 커밋, PR, 필수 검사 결과와 실행 링크, `development.md` 기록 위치 |

- 식별: 이 워크플로(github-actions)가 만들고 `openspec` 라벨과 본문 첫 줄의 `<!-- openspec-change: <id> -->`가 있는 Issue만 인정한다. 담당자는 멘션하지 않고 Assignee로만 지정한다.
- 규칙:

  | 저장소 상태 | Issue 처리 |
  |---|---|
  | 진행 중 | 없으면 만든다. 열려 있으면 자동 구역만 갱신하고, 사람이 체크한 항목과 근거 섹션은 보존한다. |
  | archive됨 | 근거를 기입한다. archive를 머지한 PR의 필수 검사(`test-backend`, `test-frontend`, `alls-green-playwright`)가 모두 success면 completed로 닫는다. master push로 돈 실행은 15분 안에 머지된 archive의 검사가 아직 돌면, 다른 Issue를 모두 처리한 뒤 한꺼번에 최대 10분 기다린다. 그래도 아니면 코멘트만 남기고 다음 실행(매시간)에서 다시 본다. |
  | 사라짐 | 사유 코멘트와 함께 not planned로 닫는다. |
  | 사람이 닫음 | 다시 열지 않는다(재오픈은 진행률을 낮춘다). |
  | Issues가 꺼진 저장소 | 아무것도 하지 않는다. |

### 4. 추적성 검사 (Harness Gate)

Harness Gate(기본 브랜치 코드, PR은 데이터로만 읽음)에 문서 검사를 더한다.

| 수준 | 조건 |
|---|---|
| 실패 (`harness/checks`) | PR이 변경을 archive했는데 `development.md` "AI 활용과 검증"에 그 변경 ID가 든 행(4칸 이상 채움)이 없음 |
| 실패 (`harness/checks`) | `prd.md`에서 상태가 `완료`인 REQ에 대해 `e2e-test.md` 실행 결과에 PASS와 40자 SHA가 있는 행이 하나도 없음 (근거 없는 완료) |
| 실패 (`harness/checks`) | PR이 바꾼 테스트 파일에 수집되지 않는 TC 표기가 있음(`TC01`·`testTC01`, TC 여러 개, `test.describe`·`test.step` 제목, 결과가 수집되지 않는 위치) |
| 실패 (`harness/checks`) | PR이 바꾼 테스트의 TC가 `e2e-test.md` 테스트 시나리오에 없음. PR이 `e2e-test.md`를 바꿨다면 모든 테스트가 대상 |
| 실패 (`harness/checks`) | PR이 archive한 변경의 AC에 TC 시나리오 행이 없거나, 종류가 `수동`이 아닌 TC에 그 이름의 테스트가 없음. tasks.md의 테스트 작업 줄(`TC-07 … <파일>::<테스트>`)에 적은 파일에 그 TC 테스트가 없음 |
| 참고 (차단 안 함) | 이번 PR이 건드린 변경에 대해: OpenSpec의 REQ·AC가 `prd.md`에 없음, 시나리오의 `연결` ID(FLOW·SEC)가 문서에 없음, 이미 archive된 변경의 AC ↔ TC ↔ 테스트 누락, proposal의 `요구사항`·`담당` 누락. 테스트·`e2e-test.md`를 바꾼 PR에서: 테스트가 없는 TC 시나리오, 수동 TC만 있는 AC, 바뀌지 않은 테스트의 TC 문제. 이번 PR에서 바뀌지 않은 근거 없는 완료 |

참고 항목은 게이트 코멘트에만 보인다. 작업 중에는 문서가 비어 있는 것이 정상이므로 막지 않는다. 예외는 두 가지다. TC를 단 테스트는 시나리오 행과 같은 커밋에 있어야 한다(테스트를 쓰는 순간 TC 번호가 정해져 있으므로). archive는 Issue를 completed로 닫으므로, archive하는 PR에서는 AC → TC → 실행되는 테스트가 끝까지 이어져야 한다. `skip`·`fixme`·`xfail`인 테스트는 실행되는 테스트로 세지 않는다.

테스트 이름 검사는 테스트 코드를 실행하지 않는다. Python은 `ast.parse`로 pytest가 수집하는 함수만 읽고, JS·TS는 주석과 문자열 안을 건너뛴다. 같은 검사를 로컬에서 `python3 -I scripts/harness/tc_check.py`(prek 훅 `tc-check`)로 돌린다. 로컬 검사는 git에 추가된 모든 테스트 파일을 이번 변경으로 보고, 기준 브랜치(`origin/master` 등)에 아직 없는 archive만 이번 archive로 본다.

### 5. 증거 수집 (`scripts/harness/collect_evidence.py`)

- CI가 테스트 결과를 남긴다. `test-backend`는 pytest `--junitxml` 결과를, `playwright`는 JSON reporter 결과를, Frontend Quality는 `frontend/evidence-reporter.ts`가 쓰는 vitest 결과(JSON)를 artifact로 올린다.
- 도구는 지정한 커밋(기본 master HEAD)의 실행과 artifact를 `gh`로 받아, TC ID별 PASS/FAIL/SKIP, 40자 SHA, 실행 시각, 실행 링크를 `e2e-test.md` 실행 결과 표 형식으로 출력한다.
- 에이전트와 사람은 이 출력만 문서에 옮긴다. 실행하지 않은 TC는 출력에 없으므로 미검증으로 남는다.

### 6. 제출 점검 (`.github/workflows/submission-check.yml`)

수동 실행이다(입력: 제출할 SHA, 기본 master HEAD). 읽기 권한만 쓰고, 결과를 job summary 체크리스트로 보여 준다.

- 40자 SHA와 해당 커밋의 필수 검사 결과
- 문서 8개 존재 여부, 템플릿 그대로인 문서(표에 행이 없음)
- `README.md`에서 문서 7개로 가는 링크
- 필수 REQ의 상태와 근거, `미검증`·`대기` 개수
- `openspec` Issue의 열림·닫힘 수
- `docs/security-policy.md` 존재 여부
- TC 연결(로컬 TC 검사와 같은 기준)

## 선택 이유

- 평가 근거는 문서에 있어야 하므로 문서를 없애거나 OpenSpec으로 대체할 수 없다. 반대로 문서만 쓰면 작업과 문서가 어긋난다. ID로 잇고 CI가 어긋남을 찾는 방식이 둘의 장점을 함께 얻는다.
- CI가 문서를 쓰지 않으므로 ruleset 예외나 봇 커밋이 필요 없다. 모든 문서 변경이 PR 리뷰를 거친다.
- 결과 숫자를 도구가 실제 CI 데이터에서 뽑으므로 "계획을 완료로 쓰지 말라"는 요구를 사람의 주의에만 맡기지 않는다.
- 형식 규칙을 `openspec/config.yaml` 한 곳에 두어 AGENTS.md·문서와 어긋나지 않게 한다.

## 검토한 대안

| 대안 | 채택하지 않은 이유 |
|---|---|
| CI가 문서 표를 자동 생성·갱신 | master 직접 push 불가. 봇 PR이 계속 쌓이고, 사람이 쓴 서술을 덮어쓸 위험이 있다. |
| `openspec show --json`을 CI에서 사용 | 파싱은 정확하지만 CI에 npm 설치(약 10초, cooldown 관리 대상)가 늘고 OpenSpec 버전에 묶인다. |
| Requirement 1개 = Issue 1개 | Issue가 많아지고, archive가 변경 단위라 요구사항별로 닫기 어렵다. |
| 추적성 문제를 모두 실패로 처리 | 작업 중에는 문서가 비어 있는 것이 정상이라 모든 PR이 막힌다. |

## 결과와 제약

- PR은 세 단계로 나눠 먼저 끝나는 것부터 머지한다.
  1. ID 규칙, 단계별 지침, AGENTS.md, 이 ADR
  2. Issue 동기화
  3. 추적성 검사, 증거 수집(테스트 결과 artifact 포함), 제출 점검
- 표 파싱은 문서 템플릿의 열 이름(`REQ`, `상태`, `TC` 등)에 의존한다. 열 이름을 바꾸면 검사도 고쳐야 한다.
- TC 결과는 `backend/tests`·`frontend/tests/e2e`·`frontend/src/**/*.test.ts`에서 테스트 이름에 TC ID를 단 경우에만 수집된다. Storybook 상호작용 테스트는 이름이 story 이름에서 나와 수집하지 않는다.
- vitest 결과를 내는 Frontend Quality는 프론트 관련 파일이 바뀐 커밋에서만 돈다(문서만 바꾼 커밋은 `workflow_dispatch`로 돌린다). JUnit은 기대 실패(`fails`)와 재시도 후 통과를 그냥 통과로 적기 때문에, 저장소의 reporter가 테스트 자신의 제목과 이 두 표시를 JSON으로 남기고 수집기는 둘 다 FAIL로 기록한다. 정적 검사는 TC를 단 `it.fails`를 막는다.
- `it.each`·`it.for`·`it.skipIf`·`it.runIf`·`test.extend`로 만든 테스트의 제목은 수집되지만 정적 검사(시나리오 행·위치)는 읽지 못한다. AC의 archive 검사는 문자 그대로의 제목만 세므로 이런 테스트만으로는 통과하지 않는다.
- 자동화할 수 없는 시험은 종류가 정확히 `수동`인 TC로 둘 수 있다. 수집 결과가 없으므로 미검증으로 남고, 근거 없는 완료 검사도 수동 TC의 PASS 행을 근거로 세지 않는다.
- 테스트 이름 검사는 문자 그대로의 제목만 읽는다. 변수·반복문으로 만든 제목, `test`를 다른 이름으로 바꿔 부른 호출, 게이트의 Python이 해석하지 못하는 문법의 파일(이 경우 `def test…` 줄만 읽음)은 정확히 알아보지 못한다.
- 이 템플릿 저장소는 Issues가 꺼져 있어 Issue 동기화의 실제 동작은 팀 저장소의 첫 실행에서 확인한다.
- `docs/security-policy.md`는 주최 측이 제공한다. 이 결정은 그 내용을 바꾸지 않는다.
