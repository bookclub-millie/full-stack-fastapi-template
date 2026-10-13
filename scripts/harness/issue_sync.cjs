// Apply the OpenSpec issue plan (scripts/harness/issue_plan.py) to GitHub Issues.
// Called from .github/workflows/openspec-issues.yml through actions/github-script.
// Rules: docs/adr/001-openspec-docs-traceability.md
//   active change   -> create the Issue, or refresh its managed part while open
//   archived change -> fill in evidence; close as completed when required checks passed
//   vanished change -> close as not planned
//   closed Issue    -> never reopened (reopening lowers the progress rate); a change
//                      proposed again after its Issue was completed gets a new Issue
// Only Issues this workflow created count: an Issue someone else opens with the
// marker line is ignored.

const LABEL = 'openspec';
const BOT = 'github-actions[bot]';
const MARKER = /^<!-- openspec-change: (\S+) -->/;
const EVIDENCE_HEADING = '## 구현·검증 근거 (작업 후 추가)';
const EVIDENCE_TEMPLATE = `${EVIDENCE_HEADING}\n커밋 주소:\n테스트 명령·결과·화면 경로:\n`;
const EMPTY_TEMPLATE_LINE = /^(커밋 주소|테스트 명령·결과·화면 경로):\s*$/;
const AUTO_START = '<!-- openspec-sync: evidence -->';
const AUTO_END = '<!-- /openspec-sync: evidence -->';
const PENDING_MARKER = '<!-- openspec-sync: evidence-pending -->';
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

// Replace only the automatic block; whatever people wrote above or below it stays as is.
function withAutoEvidence(evidence, lines) {
  const block = [AUTO_START, ...lines, AUTO_END].join('\n');
  const start = evidence.indexOf(AUTO_START);
  const end = evidence.indexOf(AUTO_END);
  if (start >= 0 && end > start) return evidence.slice(0, start) + block + evidence.slice(end + AUTO_END.length);
  const own = evidence.split('\n').filter((line) => !EMPTY_TEMPLATE_LINE.test(line.trim()));
  return `${own.join('\n').trimEnd()}\n${block}\n`;
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
      owner, repo, name: LABEL, color: '1d76db', description: 'OpenSpec 변경과 동기화되는 개발 작업 Issue (라벨을 지우지 마세요)',
    });
  }

  const byChange = new Map();
  const issues = await github.paginate(github.rest.issues.listForRepo, {
    owner, repo, state: 'all', labels: LABEL, per_page: 100,
  });
  for (const issue of issues) {
    if (issue.pull_request || issue.user?.login !== BOT) continue;
    const match = MARKER.exec(normalize(issue.body));
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

  const pendingComment = async (number) => {
    const comments = await github.paginate(github.rest.issues.listComments, { owner, repo, issue_number: number, per_page: 100 });
    return comments.find((c) => c.user?.login === BOT && c.body?.startsWith(PENDING_MARKER));
  };

  const setPendingComment = async (number, body, { createIfMissing = true } = {}) => {
    const existing = await pendingComment(number);
    const text = `${PENDING_MARKER}\n${body}`;
    if (existing?.body === text) return;
    if (existing) await github.rest.issues.updateComment({ owner, repo, comment_id: existing.id, body: text });
    else if (createIfMissing) await github.rest.issues.createComment({ owner, repo, issue_number: number, body: text });
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

  const closeNotPlanned = async (issue, reason) => {
    await github.rest.issues.createComment({ owner, repo, issue_number: issue.number, body: reason });
    await github.rest.issues.update({ owner, repo, issue_number: issue.number, state: 'closed', state_reason: 'not_planned' });
    summary.notPlanned.push(issue.number);
  };

  const complete = async (issue, change) => {
    if (!change.archive_commit) {
      await setPendingComment(issue.number, 'archive 커밋을 찾을 수 없어 완료 처리를 보류합니다.');
      summary.pending.push(issue.number);
      return;
    }
    const { managed, evidence } = splitBody(issue.body);
    const pr = await mergedPullFor(change.archive_commit);
    const results = await checkResults(pr ? pr.head.sha : change.archive_commit);
    const passed = results.every((r) => r.conclusion === 'success');
    const auto = [
      `커밋 주소: ${repoUrl}/commit/${change.archive_commit}`,
      ...(pr ? [`PR: #${pr.number}`] : []),
      '테스트 명령·결과·화면 경로:',
      ...results.map((r) => `- ${r.name}: ${r.conclusion}${r.url ? ` — ${r.url}` : ''}`),
      '- 시험 실행 기록: docs/e2e-test.md 실행 결과 · AI 활용 기록: docs/development.md',
    ];
    const body = joinBody(passed ? tickAll(managed) : managed, withAutoEvidence(evidence, auto));
    if (passed) {
      // Body and state in one call, so a failure can't leave a ticked-but-open Issue.
      await github.rest.issues.update({ owner, repo, issue_number: issue.number, body, state: 'closed', state_reason: 'completed' });
      await setPendingComment(issue.number, '필수 검사가 모두 success가 되어 완료로 닫았습니다.', { createIfMissing: false });
      summary.completed.push(issue.number);
      return;
    }
    if (body !== normalize(issue.body)) await github.rest.issues.update({ owner, repo, issue_number: issue.number, body });
    const failing = results.filter((r) => r.conclusion !== 'success').map((r) => `${r.name}: ${r.conclusion}`);
    await setPendingComment(
      issue.number,
      `필수 검사가 모두 success가 아니라 완료 처리를 보류합니다 (${failing.join(', ')}). 다음 동기화 때 다시 확인합니다.`,
    );
    summary.pending.push(issue.number);
  };

  const planned = new Set(plan.changes.map((c) => c.id));
  for (const change of plan.changes) {
    const existing = byChange.get(change.id) || [];
    const open = existing.filter((i) => i.state === 'open').sort((a, b) => a.number - b.number);
    const closed = existing.filter((i) => i.state === 'closed');
    let issue = open[0];

    for (const duplicate of open.slice(1)) {
      await closeNotPlanned(duplicate, `같은 OpenSpec 변경 \`${change.id}\`의 중복 Issue라 not planned로 닫습니다 (#${issue.number}에서 관리).`);
    }

    if (!issue) {
      const lastClosed = Math.max(0, ...closed.map((i) => Date.parse(i.closed_at) || 0));
      const reproposed =
        !change.archived &&
        closed.length > 0 &&
        closed.every((i) => i.state_reason === 'completed') &&
        Date.parse(change.proposal_date) > lastClosed;
      if (closed.length && !reproposed) {
        summary.skipped.push(...closed.map((i) => i.number));
        continue;
      }
      const assignee = await assigneeFor(change);
      ({ data: issue } = await github.rest.issues.create({
        owner, repo, title: change.title, labels: [LABEL], body: joinBody(change.managed, EVIDENCE_TEMPLATE),
        ...(assignee ? { assignees: [assignee] } : {}),
      }));
      summary.created.push(issue.number);
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
      await closeNotPlanned(issue, `OpenSpec 변경 \`${id}\`이 archive 없이 저장소에서 사라져 not planned로 닫습니다 (기준 커밋 ${context.sha}).`);
    }
  }

  core.info(`OpenSpec issue sync: ${JSON.stringify(summary)}`);
  return summary;
};

module.exports.splitBody = splitBody;
module.exports.keepTicks = keepTicks;
module.exports.withAutoEvidence = withAutoEvidence;
