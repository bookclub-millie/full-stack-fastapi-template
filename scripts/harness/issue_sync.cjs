// Apply the OpenSpec issue plan (scripts/harness/issue_plan.py) to GitHub Issues.
// Called from .github/workflows/openspec-issues.yml through actions/github-script.
// Rules: docs/adr/001-openspec-docs-traceability.md
//   active change   -> create the Issue, or refresh its managed part while open
//   archived change -> fill in evidence; close as completed when required checks passed
//   vanished change -> close as not planned
//   closed Issue    -> never reopened (reopening lowers the progress rate)

const LABEL = 'openspec';
const MARKER = /^<!-- openspec-change: (\S+) -->/;
const EVIDENCE_HEADING = '## 구현·검증 근거 (작업 후 추가)';
const EVIDENCE_TEMPLATE = `${EVIDENCE_HEADING}\n커밋 주소:\n테스트 명령·결과·화면 경로:\n`;
const PENDING_MARKER = '<!-- openspec-sync: evidence-pending -->';
const AUTO_EVIDENCE = '<!-- openspec-sync: evidence -->';
const MAX_NOT_PLANNED = 5;

// Bodies edited in the web UI come back with CRLF line endings.
function normalize(body) {
  return (body || '').replace(/\r\n/g, '\n');
}

function splitBody(body) {
  const text = normalize(body);
  const at = text.indexOf(EVIDENCE_HEADING);
  if (at < 0) return { managed: `${text.trimEnd()}\n`, evidence: EVIDENCE_TEMPLATE };
  return { managed: `${text.slice(0, at).trimEnd()}\n`, evidence: text.slice(at) };
}

function joinBody(managed, evidence) {
  return `${managed.trimEnd()}\n\n${evidence.trimEnd()}\n`;
}

// Keep boxes that a person already ticked for the same item.
function keepTicks(managed, previous) {
  const ticked = new Set([...previous.matchAll(/^- \[[xX]\] (.+)$/gm)].map((m) => m[1].trim()));
  return managed.replace(/^- \[ \] (.+)$/gm, (line, item) => (ticked.has(item.trim()) ? `- [x] ${item}` : line));
}

function tickAll(managed) {
  return managed.replace(/^- \[ \] /gm, '- [x] ');
}

// Lines a person added under the evidence heading (not the empty template lines).
function humanEvidence(evidence) {
  const auto = evidence.indexOf(AUTO_EVIDENCE);
  const own = auto >= 0 ? evidence.slice(0, auto) : evidence;
  return own
    .split('\n')
    .slice(1)
    .filter((line) => line.trim() && !/^(커밋 주소|테스트 명령·결과·화면 경로):\s*$/.test(line.trim()));
}

module.exports = async function syncIssues({ github, context, core, plan, requiredChecks }) {
  const { owner, repo } = context.repo;
  const repoUrl = `${context.serverUrl}/${owner}/${repo}`;
  const summary = { created: [], updated: [], completed: [], pending: [], notPlanned: [], skipped: [] };

  const { data: repository } = await github.rest.repos.get({ owner, repo });
  if (!repository.has_issues) {
    core.notice('Issues are disabled in this repository; nothing to sync.');
    return summary;
  }
  if (context.ref && context.ref !== `refs/heads/${repository.default_branch}`) {
    core.notice(`Runs only on ${repository.default_branch}; got ${context.ref}.`);
    return summary;
  }

  try {
    await github.rest.issues.getLabel({ owner, repo, name: LABEL });
  } catch (error) {
    if (error.status !== 404) throw error;
    await github.rest.issues.createLabel({
      owner, repo, name: LABEL, color: '1d76db', description: 'OpenSpec 변경과 동기화되는 개발 작업 Issue',
    });
  }

  const byChange = new Map();
  const issues = await github.paginate(github.rest.issues.listForRepo, { owner, repo, state: 'all', per_page: 100 });
  for (const issue of issues) {
    if (issue.pull_request) continue;
    const match = MARKER.exec(issue.body || '');
    if (!match) continue;
    if (!byChange.has(match[1])) byChange.set(match[1], []);
    byChange.get(match[1]).push(issue);
  }

  const canAssign = async (login) => {
    if (!login) return false;
    try {
      await github.rest.issues.checkUserCanBeAssigned({ owner, repo, assignee: login });
      return true;
    } catch (error) {
      if (error.status === 404) return false;
      throw error;
    }
  };

  const mergedPullFor = async (sha) => {
    if (!sha) return null;
    const { data } = await github.rest.repos.listPullRequestsAssociatedWithCommit({ owner, repo, commit_sha: sha });
    return data.find((pr) => pr.merged_at) || null;
  };

  const assigneeFor = async (change) => {
    if (await canAssign(change.owner)) return change.owner;
    const pr = await mergedPullFor(change.proposal_commit);
    const author = pr?.user?.type === 'User' ? pr.user.login : null;
    return (await canAssign(author)) ? author : null;
  };

  const upsertPendingComment = async (number, body) => {
    const comments = await github.paginate(github.rest.issues.listComments, { owner, repo, issue_number: number, per_page: 100 });
    const existing = comments.find((c) => c.user?.login === 'github-actions[bot]' && c.body?.startsWith(PENDING_MARKER));
    const text = `${PENDING_MARKER}\n${body}`;
    if (existing?.body === text) return;
    if (existing) await github.rest.issues.updateComment({ owner, repo, comment_id: existing.id, body: text });
    else await github.rest.issues.createComment({ owner, repo, issue_number: number, body: text });
  };

  const checkResults = async (ref) => {
    const runs = await github.paginate(github.rest.checks.listForRef, { owner, repo, ref, per_page: 100 });
    const latest = new Map();
    for (const run of runs) {
      const seen = latest.get(run.name);
      if (!seen || run.id > seen.id) latest.set(run.name, run);
    }
    return requiredChecks.map((name) => {
      const run = latest.get(name);
      return { name, conclusion: run ? run.conclusion || run.status : 'missing', url: run?.html_url };
    });
  };

  const complete = async (issue, change) => {
    const { managed, evidence } = splitBody(issue.body);
    if (!change.archive_commit) {
      await upsertPendingComment(issue.number, 'archive 커밋을 찾을 수 없어 완료 처리를 보류합니다.');
      summary.pending.push(issue.number);
      return;
    }
    const pr = await mergedPullFor(change.archive_commit);
    const results = await checkResults(pr ? pr.head.sha : change.archive_commit);
    const lines = [
      EVIDENCE_HEADING,
      ...humanEvidence(evidence),
      AUTO_EVIDENCE,
      `커밋 주소: ${repoUrl}/commit/${change.archive_commit}`,
      ...(pr ? [`PR: #${pr.number}`] : []),
      '테스트 명령·결과·화면 경로:',
      ...results.map((r) => `- ${r.name}: ${r.conclusion}${r.url ? ` — ${r.url}` : ''}`),
      '- 시험 실행 기록: docs/e2e-test.md 실행 결과 · AI 활용 기록: docs/development.md',
    ];
    const passed = results.every((r) => r.conclusion === 'success');
    const body = joinBody(passed ? tickAll(managed) : managed, lines.join('\n'));
    if (body !== normalize(issue.body)) await github.rest.issues.update({ owner, repo, issue_number: issue.number, body });
    if (!passed) {
      const failing = results.filter((r) => r.conclusion !== 'success').map((r) => `${r.name}: ${r.conclusion}`);
      await upsertPendingComment(
        issue.number,
        `필수 검사가 모두 success가 아니라 완료 처리를 보류합니다 (${failing.join(', ')}). 다음 동기화 때 다시 확인합니다.`,
      );
      summary.pending.push(issue.number);
      return;
    }
    await github.rest.issues.update({ owner, repo, issue_number: issue.number, state: 'closed', state_reason: 'completed' });
    summary.completed.push(issue.number);
  };

  const planned = new Set(plan.changes.map((c) => c.id));
  for (const change of plan.changes) {
    const existing = (byChange.get(change.id) || []).sort(
      (a, b) => (a.state === 'open' ? 0 : 1) - (b.state === 'open' ? 0 : 1) || a.number - b.number,
    );
    let issue = existing[0];
    if (!issue) {
      const assignee = await assigneeFor(change);
      ({ data: issue } = await github.rest.issues.create({
        owner, repo, title: change.title, labels: [LABEL], body: joinBody(change.managed, EVIDENCE_TEMPLATE),
        ...(assignee ? { assignees: [assignee] } : {}),
      }));
      summary.created.push(issue.number);
    } else if (issue.state === 'closed') {
      summary.skipped.push(issue.number);
      continue;
    } else {
      const { managed, evidence } = splitBody(issue.body);
      const body = joinBody(keepTicks(change.managed, managed), evidence);
      if (body !== normalize(issue.body) || change.title !== issue.title) {
        ({ data: issue } = await github.rest.issues.update({ owner, repo, issue_number: issue.number, title: change.title, body }));
        summary.updated.push(issue.number);
      }
    }
    if (change.archived) await complete(issue, change);
  }

  const vanished = [...byChange.entries()]
    .filter(([id]) => !planned.has(id))
    .flatMap(([id, list]) => list.filter((i) => i.state === 'open').map((issue) => ({ id, issue })));
  if (vanished.length && !plan.openspec_present) {
    core.warning('openspec/changes is missing; not closing any Issue.');
  } else if (vanished.length > MAX_NOT_PLANNED) {
    core.warning(`${vanished.length} Issues lost their OpenSpec change; close them by hand if that is intended.`);
  } else {
    for (const { id, issue } of vanished) {
      await github.rest.issues.createComment({
        owner, repo, issue_number: issue.number,
        body: `OpenSpec 변경 \`${id}\`이 archive 없이 저장소에서 사라져 not planned로 닫습니다 (기준 커밋 ${context.sha}).`,
      });
      await github.rest.issues.update({ owner, repo, issue_number: issue.number, state: 'closed', state_reason: 'not_planned' });
      summary.notPlanned.push(issue.number);
    }
  }

  core.info(`OpenSpec issue sync: ${JSON.stringify(summary)}`);
  return summary;
};

module.exports.splitBody = splitBody;
module.exports.keepTicks = keepTicks;
module.exports.humanEvidence = humanEvidence;
