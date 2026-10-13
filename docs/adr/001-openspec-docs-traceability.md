# ADR-001: OpenSpec과 문서·Issue 연동

- 상태: 채택
- 날짜: 2026-10-14
- 관련 REQ·Issue·PR: #1(CI 하네스), #3(OpenSpec 설정)

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
| 테스트 이름 | pytest `test_tc_01_...`, Playwright `test("TC-01 ...")` | `e2e-test.md` TC와 실행 결과 |

REQ·AC·FLOW·TC 번호는 저장소 전체에서 하나씩 증가시킨다. 새 번호는 `prd.md`·`experience.md`·`e2e-test.md`에 있는 가장 큰 번호 다음을 쓴다.

### 2. 단계별 문서 갱신 (`openspec/config.yaml` 규칙·지침, `AGENTS.md`)

| 단계 | 할 일 |
|---|---|
| propose | tasks.md의 마지막 그룹을 **문서·근거**로 둔다: `prd.md` 추적표 행(상태 `계획`), `experience.md` FLOW, `e2e-test.md` TC 시나리오(상태 `미검증`), 해당하면 `security-compliance.md` SEC 행, 저장소 전체 결정이면 ADR. |
| apply | 구현과 함께 TC ID를 단 테스트를 작성한다. 문서·근거 그룹 작업을 수행한다. |
| archive | 증거 수집 도구(5번)의 출력으로 `e2e-test.md` 실행 결과를 채운다. `prd.md`·`experience.md`·`security-compliance.md` 상태를 실제 결과로 바꾼다. `development.md` "AI 활용과 검증"에 이 변경의 행을 추가한다. |

`AGENTS.md`에는 "기능·동작 변경은 OpenSpec으로 시작한다, Issue는 손으로 만들거나 닫지 않는다, 결과는 증거 수집 도구의 출력만 옮긴다" 수준의 짧은 규칙만 둔다. 형식 규칙은 `openspec/config.yaml` 한 곳에만 둔다.

### 3. Issue 동기화 (`.github/workflows/openspec-issues.yml`)

- 실행: master push(`openspec/**`), 수동 실행, 하루 1회. master의 코드만 실행한다. 권한은 `issues: write`, `contents·pull-requests·checks: read`.
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
  | archive됨 | 근거를 기입한다. archive를 머지한 PR의 필수 검사(`test-backend`, `test-frontend`, `alls-green-playwright`)가 모두 success면 completed로 닫는다. 아니면 코멘트만 남기고 다음 실행에서 다시 본다. |
  | 사라짐 | 사유 코멘트와 함께 not planned로 닫는다. |
  | 사람이 닫음 | 다시 열지 않는다(재오픈은 진행률을 낮춘다). |
  | Issues가 꺼진 저장소 | 아무것도 하지 않는다. |

### 4. 추적성 검사 (Harness Gate)

Harness Gate(기본 브랜치 코드, PR은 데이터로만 읽음)에 문서 검사를 더한다.

| 수준 | 조건 |
|---|---|
| 실패 (`harness/checks`) | PR이 변경을 archive했는데 `development.md` "AI 활용과 검증"에 그 변경 ID가 든 행(4칸 이상 채움)이 없음 |
| 실패 (`harness/checks`) | `prd.md`에서 상태가 `완료`인 REQ에 대해 `e2e-test.md` 실행 결과에 PASS와 40자 SHA가 있는 행이 하나도 없음 (근거 없는 완료) |
| 참고 (차단 안 함) | OpenSpec의 REQ·AC가 문서에 없음, 문서의 REQ가 OpenSpec에 없음, 정의되지 않은 ID 참조, archive된 변경의 AC에 TC가 없음 |

참고 항목은 게이트 코멘트에만 보인다. 작업 중에는 문서가 비어 있는 것이 정상이므로 막지 않는다.

### 5. 증거 수집 (`scripts/evidence/collect.py`)

- CI가 테스트 결과를 남긴다. `test-backend`는 pytest `--junitxml` 결과를, `playwright`는 JSON reporter 결과를 artifact로 올린다.
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
- TC 결과는 테스트 이름에 TC ID를 단 경우에만 수집된다.
- 이 템플릿 저장소는 Issues가 꺼져 있어 Issue 동기화의 실제 동작은 팀 저장소의 첫 실행에서 확인한다.
- `docs/security-policy.md`는 주최 측이 제공한다. 이 결정은 그 내용을 바꾸지 않는다.
