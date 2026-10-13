# CI 하네스

AI 코딩 에이전트와 함께 개발할 때 PR이 머지되기 전에 무엇을 자동으로 막고, 무엇을 사람이 확인하는지 정리한다. 에이전트용 작업 규칙은 [AGENTS.md](../AGENTS.md)에 있다.

## 원칙

- **판정 코드는 PR이 바꿀 수 없다.** Harness Gate는 기본 브랜치의 검사 코드로 PR을 판정한다. PR이 검사 스크립트를 고쳐도 그 PR의 판정에는 반영되지 않는다.
- **PR 내용은 데이터로만 읽는다.** 게이트는 PR의 코드를 설치·빌드·실행하지 않는다. 도구(gitleaks, zizmor)는 네트워크가 없는 컨테이너에서 읽기 전용으로 돌린다.
- **결정적 검사는 막고, 휴리스틱 신호는 사람에게 넘긴다.** 오탐이 거의 없는 검사는 실패로 처리한다. 정당한 변경일 수도 있는 신호는 PR 작성자가 아닌 사람이 확인하면 통과한다.
- **AI 리뷰는 참고용이다.** 필수 체크가 아니고 승인도 하지 않는다. 모델에는 쓰기 권한과 셸을 주지 않는다.

## 구성

| 구성 요소 | 실행 시점 | 신뢰 경계 | 필수 체크 |
|---|---|---|---|
| [Harness Gate](../.github/workflows/harness-gate.yml) | PR 열림·push·라벨 | 기본 브랜치 코드, PR은 데이터 | `harness/checks`, `harness/ack` |
| [Test Frontend](../.github/workflows/test-frontend.yml) | PR·master push | PR 코드 실행, 비밀값 없음 | `test-frontend` |
| [Test Backend](../.github/workflows/test-backend.yml) | PR·master push | PR 코드 실행, 비밀값 없음 | `test-backend` |
| [AI Review](../.github/workflows/ai-review.yml) | 같은 저장소의 사람 PR | 모델 job은 읽기 전용, 게시 job은 모델 없음 | 아니요 |
| [OpenSpec Issues](../.github/workflows/openspec-issues.yml) | master push(`openspec/**`)·매일·수동 | 기본 브랜치 코드, Issue 쓰기 권한 | 아니요 |
| [Test Harness](../.github/workflows/test-harness.yml) | `scripts/harness/` 변경 | PR 코드 실행 | 아니요 |
| [Zizmor](../.github/workflows/zizmor.yml) | PR·master push | PR 코드를 정적 분석 | 아니요 (게이트가 다시 검사) |
| `bunfig.toml`, `pyproject.toml` | 로컬·CI 의존성 해석 | — | — |
| [ruleset](../scripts/harness/ruleset.json), [설정 스크립트](../scripts/harness/setup-repo.sh) | 저장소마다 1회 | 관리자 | — |

## 결정적 검사 — `harness/checks`

하나라도 실패하면 머지할 수 없다. 사람이 확인해도 넘길 수 없으므로 원인을 고친 커밋을 push한다.

| 검사 | 실패 조건 |
|---|---|
| 비밀값 스캔 | PR 커밋 범위(merge base..head)에서 gitleaks가 비밀값을 찾음. PR이 올린 `.gitleaksignore`·`gitleaks:allow` 주석은 무시한다. |
| 워크플로 보안 | `.github/`가 바뀐 PR에서 zizmor가 문제를 찾음. 예: SHA로 고정하지 않은 action, 템플릿 인젝션, 과도한 권한. |
| 공급망 | lockfile에 새로 들어온 버전이 출시 7일 미만임. 레지스트리 밖 소스(git·URL·사설 레지스트리)를 씀. 레지스트리에 없는 패키지가 있음. cooldown 설정을 끄거나 7일 미만으로 줄임. 레지스트리 조회에 실패해도 실패로 처리한다. |

## 사람 확인 신호 — `harness/ack`

| 신호 | 예 |
|---|---|
| 하네스·CI·에이전트 설정 변경 | `.github/`, `scripts/harness/`, `AGENTS.md`, `CLAUDE.md`, `.claude/`, `bunfig.toml`, `exclude-newer` |
| 테스트 감소 | 테스트 파일 삭제·이동, 테스트 함수 수 감소, assertion 수 감소 |
| skip·focus 마커 | `pytest.mark.skip`, `xfail`, `test.skip`, `test.only`, `fixme` |
| 테스트·커버리지 설정 변경 | `--fail-under`, `addopts`, `playwright.config.ts`, 테스트 스크립트 |
| 검사 억제 | `# type: ignore`, `# noqa`, `@ts-ignore`, `eslint-disable`, `biome-ignore` |
| 광범위한 예외 처리 | `except:`, `except Exception:` |
| 새 직접 의존성 | `package.json`·`pyproject.toml`에 새 이름 |
| 최근 등록 패키지 | lockfile에 새로 들어온 패키지 중 레지스트리 첫 등록이 30일 이내 |

신호가 있으면 게이트가 PR에 요약 코멘트를 단다. 통과 절차는 다음과 같다.

1. PR 작성자가 PR 설명에 변경 이유를 적는다.
2. PR 작성자가 아닌, write 이상 권한을 가진 사람이 diff를 확인하고 `harness-ack` 라벨을 붙인다.
3. 게이트가 라벨을 붙인 사람을 검증하고 `harness/ack`를 통과로 바꾼다. 봇·앱이 붙인 라벨과 작성자 본인의 라벨은 인정하지 않는다.
4. 이후 새 커밋이 push되면 라벨이 자동으로 해제된다. 새 diff를 다시 확인해야 한다.

ruleset은 이와 별도로 마지막 push를 한 사람이 아닌 사람의 승인 1건을 요구한다.

## AI 리뷰

- 같은 저장소 브랜치에서 사람이 연 PR에만 돈다. fork PR과 봇 PR은 건너뛴다.
- 모델 job: `contents: read`, `pull-requests: read`만 쓴다. 도구는 Read·Glob·Grep만 허용하고, Bash·쓰기·웹 접근과 `/proc` 등 작업 폴더 밖 읽기는 막는다. 프롬프트에는 PR 번호만 넣고 제목·본문·코멘트는 넣지 않는다. 결과는 JSON 스키마로만 받는다.
- 게시 job: 모델 없이 JSON을 검증한다. PR에 없는 파일을 가리키는 지적은 버린다. 링크·멘션·HTML·비밀값 형태를 제거한 뒤 코멘트 하나를 갱신한다.
- reward hacking도 함께 판단하게 한다. 테스트 입력 하드코딩처럼 diff 규칙으로 잡기 어려운 경우를 보완하기 위해서다.
- `ai-review` environment에 `ANTHROPIC_API_KEY`가 없으면 건너뛴다.

## OpenSpec Issue 동기화

OpenSpec 변경 하나를 개발 작업 Issue 하나로 맞춘다([ADR-001](adr/001-openspec-docs-traceability.md)).

| OpenSpec 상태 (master 기준) | Issue 처리 |
|---|---|
| 제안이 머지됨 | `[REQ-xx] 기능 이름` Issue를 만든다. 목적·완료 조건(AC)·담당자·연결 문서를 채우고 `openspec` 라벨을 단다. |
| 제안이 바뀜 | 열린 Issue의 자동 구역만 갱신한다. 사람이 체크한 항목과 근거 섹션은 그대로 둔다. |
| archive가 머지됨 | 근거(커밋, PR, `test-backend`·`test-frontend`·`alls-green-playwright` 결과)를 적는다. 모두 success면 Close as completed로 닫고, 아니면 보류 코멘트를 남기고 매일 다시 확인한다. |
| archive 없이 삭제됨 | 사유를 남기고 Close as not planned로 닫는다. 한 번에 6건 이상이면 닫지 않고 경고만 낸다. |
| 사람이 닫음 | 다시 열지 않는다. |

- Issue는 이 워크플로가 만든 것 중 `openspec` 라벨과 본문 첫 줄의 `<!-- openspec-change: <id> -->`가 있는 것만 인정한다. 라벨이나 이 줄을 지우면 새 Issue가 생긴다. 다른 사람이 같은 줄을 넣어 만든 Issue는 무시한다.
- 같은 변경에 열린 Issue가 둘 이상이면 번호가 가장 작은 것만 남기고 나머지는 중복으로 not planned 처리한다. completed로 닫힌 변경을 다시 제안하면 새 Issue를 만든다.
- 근거 섹션에서 자동으로 채우는 부분은 `<!-- openspec-sync: evidence -->` 블록뿐이다. 그 위아래에 직접 쓴 내용은 그대로 둔다.
- Issues가 꺼진 저장소(이 템플릿)에서는 아무것도 하지 않는다.
- 계획은 `scripts/harness/issue_plan.py`(토큰 없음), 반영은 `scripts/harness/issue_sync.cjs`가 한다.

## 출시 7일 cooldown과 예외

- 로컬과 CI에서 의존성을 새로 해석할 때 `bunfig.toml`의 `minimumReleaseAge = 604800`, `pyproject.toml`의 `exclude-newer = "7 days"`가 출시 7일 미만 버전을 고르지 않게 한다. Dependabot도 같은 7일 cooldown을 쓴다.
- `bun ci`는 lockfile에 이미 있는 버전의 나이를 다시 확인하지 않는다. 그래서 게이트가 lockfile diff를 레지스트리에 직접 조회한다.
- Dependabot cooldown은 보안 업데이트에 적용되지 않는다. 급한 보안 패치는 다음처럼 예외를 둔다. 예외 변경은 `harness-config` 신호로 사람 확인을 받는다.
  - bun: `bunfig.toml`의 `minimumReleaseAgeExcludes = ["패키지명"]` (정확한 이름만 가능)
  - uv: `pyproject.toml`의 `[tool.uv] exclude-newer-package = { 패키지명 = false }` 후 `uv lock`
- 패치가 7일을 넘기면 예외를 지운다.
- uv는 `"1 month"`처럼 해석할 수 없는 값을 경고만 내고 무시한다. 그래서 게이트는 `uv.lock`의 `exclude-newer-span`도 확인한다.

## 저장소 설정 (템플릿으로 만든 저장소마다 1회)

템플릿으로 저장소를 만들면 파일만 복사되고 라벨·ruleset·environment·Actions 설정은 복사되지 않는다. 저장소 관리자가 다음을 실행한다.

```bash
bash scripts/harness/setup-repo.sh owner/repo
gh secret set ANTHROPIC_API_KEY --env ai-review --repo owner/repo   # AI 리뷰를 쓸 때
```

스크립트가 적용하는 설정은 다음과 같다.

- `GITHUB_TOKEN` 기본 권한을 읽기 전용으로 바꾸고, PR 승인 권한을 끈다.
- SHA로 고정하지 않은 action 사용을 막는다.
- 외부 기여자의 fork PR 워크플로는 실행 전에 승인을 요구한다.
- `harness-ack` 라벨과 `ai-review` environment를 만든다.
- 기본 브랜치 ruleset을 만든다.
  - 승인 1건이 필요하고, 마지막 push는 다른 사람이 승인해야 한다.
  - push가 있으면 기존 승인을 무효로 한다.
  - 필수 체크는 `harness/checks`, `harness/ack`, `test-backend`, `test-frontend`다.
  - force push와 브랜치 삭제를 금지한다.
  - 우회 권한자는 두지 않는다.

필수 체크를 늘리려면 [ruleset.json](../scripts/harness/ruleset.json)에 체크 이름을 추가하고 스크립트를 다시 실행한다.

## CI 시간

- 하네스 job들은 서로, 그리고 기존 테스트와 병렬로 돈다.
- 게이트의 분석 단계는 이 저장소의 실제 커밋 기준으로 측정했다(로컬). 의존성 변경이 없으면 1초 미만, npm 의존성 수십 개를 바꾼 Dependabot 커밋은 약 6.5초였다.
- 레지스트리 조회는 lockfile이 바뀐 PR에서만 한다. zizmor는 `.github/`가 바뀐 PR에서만 돈다.
- Test Frontend는 프론트 관련 파일이 바뀌지 않으면 설치와 검사를 건너뛰고 바로 통과한다. 로컬 측정은 typecheck 4.7초, KDS lint 1.8초, vite build 1.3초다. build 스크립트가 tsc를 한 번 더 돌리는 중복은 뺐다.
- 같은 PR에 새 push가 오면 Test Frontend·AI Review의 이전 실행은 취소된다.
- GitHub 러너에서 잰 시간은 아직 없다. 실제 소요 시간은 첫 PR 실행 후 기록한다.

## 한계

- **write 권한자의 의도적인 위조는 막지 못한다.** commit status는 write 권한자나 그 권한으로 도는 워크플로가 같은 이름으로 덮어쓸 수 있다. ruleset의 사람 승인(마지막 push를 하지 않은 사람)이 마지막 방어선이다. 이 하네스는 에이전트의 무심한 reward hacking과 외부 기여 위험을 줄이는 장치이고, 악의적인 내부자는 범위 밖이다.
- **휴리스틱에는 오탐과 미탐이 있다.** 예를 들어 테스트 입력을 하드코딩한 제품 코드는 diff 규칙으로 잡기 어렵다. AI 리뷰와 사람 리뷰로 보완한다.
- **AI 리뷰는 여전히 PR 내용에 담긴 프롬프트 인젝션의 영향을 받는다.** 영향 범위는 참고용 코멘트 하나로 제한했다.
- **게이트를 바꾸는 PR은 머지된 뒤부터 적용된다.** cooldown을 낮추는 변경은 이전 규칙에 막히므로, 검사 코드를 바꾸는 PR을 먼저 머지한 뒤 설정을 바꾼다.

## 유지보수

| 대상 | 갱신 방법 |
|---|---|
| 워크플로의 action SHA | Dependabot `github-actions` (7일 cooldown) |
| gitleaks·zizmor 컨테이너 digest (`harness-gate.yml` env) | 수동. 새 버전이 7일 지난 뒤 `docker buildx imagetools inspect <image>:<tag>`로 digest를 확인해 교체한다. |
| `claude-code-action` | Dependabot. 갱신 PR은 `harness-config` 신호로 사람 확인을 받는다. |
| 검사 규칙 (`scripts/harness/`) | 테스트(`python3 -I -m unittest discover -s scripts/harness/tests -t scripts/harness`)와 함께 수정한다. |

## 참고 자료

- [Risks and mitigations for GitHub Copilot cloud agent](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/risks-and-mitigations)
- [CSA: Claude Code GitHub Action prompt injection](https://labs.cloudsecurityalliance.org/research/csa-research-note-claude-code-github-action-prompt-injection/)
- [Aikido: PromptPwnd](https://www.aikido.dev/blog/promptpwnd-github-actions-ai-agents)
- [VentureBeat: Comment and Control](https://venturebeat.com/security/ai-agent-runtime-security-system-card-audit-comment-and-control-2026)
- [Agentic Workflow Injection in GitHub Actions](https://arxiv.org/html/2605.07135v1)
- [pnpm: minimumReleaseAge, trustPolicy](https://pnpm.io/settings/dependency-resolution)
- [Simon Willison: Package managers need to cool down](https://simonwillison.net/2026/Mar/24/package-managers-need-to-cool-down/)
- [Classmethod: pnpm 11 minimumReleaseAge와 Dependabot CI 실패](https://dev.classmethod.jp/en/articles/pnpm-11-minimum-release-age-dependabot-ci-failure/)
- [CSA: Slopsquatting](https://labs.cloudsecurityalliance.org/research-rb/csa-research-note-slopsquatting-ai-coding-assistant-supply-c/)
- [Packagist: Securing GitHub Actions workflows with zizmor](https://blog.packagist.com/securing-our-github-actions-workflows-with-zizmor/)
- [Responding to the tj-actions compromise](https://www.softwareseni.com/responding-to-the-tj-actions-github-actions-compromise-and-preventing-tag-based-supply-chain-attacks)
- [EvilGenie: a Reward Hacking Benchmark](https://alphaxiv.org/abs/2511.21654)
- [Axon Build: Guardrails for AI coding agents](https://axonbuild.com/blog/guardrails-for-ai-coding-agents)
- [How to run AI coding agents in CI/CD: a 2026 guide](https://andrew.ooo/answers/how-to-run-ai-coding-agents-in-ci-cd-2026-guide/)
- [OpenSSF: Security-Focused Guide for AI Code Assistant Instructions](https://best.openssf.org/Security-Focused-Guide-for-AI-Code-Assistant-Instructions)
