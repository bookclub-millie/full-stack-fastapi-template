// Scenario tests for issue_sync.cjs against an in-memory GitHub API.
// Run: node --test scripts/harness/tests/
const test = require('node:test')
const assert = require('node:assert/strict')
const syncIssues = require('../issue_sync.cjs')

const REQUIRED = ['test-backend', 'test-frontend', 'alls-green-playwright']
const BOT = { login: 'github-actions[bot]' }
const notFound = () => Object.assign(new Error('Not Found'), { status: 404 })

function fakeGitHub({
  issues = [],
  hasIssues = true,
  checks = {},
  pulls = {},
  assignable = ['gray'],
  comments = {}
} = {}) {
  const state = {
    issues: issues.map(i => ({ state: 'open', title: '', user: BOT, ...i })),
    labels: new Set(),
    comments,
    calls: []
  }
  let nextNumber = Math.max(0, ...state.issues.map(i => i.number)) + 1
  const find = number => state.issues.find(i => i.number === number)
  const github = {
    paginate: async (fn, params) => (await fn(params)).data,
    rest: {
      repos: {
        get: async () => ({
          data: { has_issues: hasIssues, default_branch: 'master' }
        }),
        listPullRequestsAssociatedWithCommit: async ({ commit_sha }) => ({
          data: pulls[commit_sha] || []
        })
      },
      checks: { listForRef: async ({ ref }) => ({ data: checks[ref] || [] }) },
      issues: {
        getLabel: async ({ name }) => {
          if (!state.labels.has(name)) throw notFound()
          return { data: {} }
        },
        createLabel: async ({ name }) => state.labels.add(name),
        listForRepo: async () => ({ data: state.issues.map(i => ({ ...i })) }),
        checkUserCanBeAssigned: async ({ assignee }) => {
          if (!assignable.includes(assignee)) throw notFound()
        },
        create: async ({ title, body, assignees }) => {
          const issue = {
            number: nextNumber++,
            title,
            body,
            assignees,
            state: 'open',
            user: BOT
          }
          state.issues.push(issue)
          state.calls.push(['create', issue.number])
          return { data: { ...issue } }
        },
        update: async ({
          owner: _owner,
          repo: _repo,
          issue_number,
          ...fields
        }) => {
          Object.assign(find(issue_number), fields)
          state.calls.push([
            'update',
            issue_number,
            Object.keys(fields).sort().join(',')
          ])
          return { data: { ...find(issue_number) } }
        },
        listComments: async ({ issue_number }) => ({
          data: state.comments[issue_number] || []
        }),
        createComment: async ({ issue_number, body }) => {
          if (!state.comments[issue_number]) state.comments[issue_number] = []
          state.comments[issue_number].push({
            id: Date.now(),
            user: { login: 'github-actions[bot]' },
            body
          })
          state.calls.push(['comment', issue_number])
        },
        updateComment: async ({ comment_id, body }) => {
          for (const list of Object.values(state.comments)) {
            const comment = list.find(c => c.id === comment_id)
            if (comment) comment.body = body
          }
          state.calls.push(['updateComment', comment_id])
        }
      }
    }
  }
  return { github, state }
}

const context = {
  repo: { owner: 'o', repo: 'r' },
  serverUrl: 'https://github.com',
  ref: 'refs/heads/master',
  sha: 'abc'
}
const core = {
  notice() {},
  info() {},
  warning(message) {
    core.warnings.push(message)
  },
  warnings: []
}

function change(overrides = {}) {
  return {
    id: 'add-todo',
    archived: false,
    title: '[REQ-01] 할 일 등록',
    managed:
      '<!-- openspec-change: add-todo -->\n## 목적\n저장한다.\n\n## 완료 조건\n- [ ] AC-01 거부한다\n- [ ] 정상·오류 테스트 결과를 남긴다\n\n## 담당자 / 연결 문서\n담당: @gray\n',
    owner: 'gray',
    proposal_commit: 'p1',
    archive_commit: null,
    ...overrides
  }
}

const run = (github, changes, extra = {}) =>
  syncIssues({
    github,
    context,
    core,
    plan: { openspec_present: true, changes },
    requiredChecks: REQUIRED,
    ...extra
  })

const passing = (names = REQUIRED) =>
  names.map((name, i) => ({
    id: i + 1,
    name,
    conclusion: 'success',
    html_url: `u/${name}`
  }))

test('creates one Issue per new change with assignee and label', async () => {
  const { github, state } = fakeGitHub()
  const summary = await run(github, [change()])
  assert.deepEqual(summary.created, [1])
  assert.equal(state.issues[0].title, '[REQ-01] 할 일 등록')
  assert.deepEqual(state.issues[0].assignees, ['gray'])
  assert.match(
    state.issues[0].body,
    /## 구현·검증 근거 \(작업 후 추가\)\n커밋 주소:\n/
  )
  assert.ok(state.labels.has('openspec'))
})

test('second run is idempotent', async () => {
  const { github, state } = fakeGitHub()
  await run(github, [change()])
  state.calls.length = 0
  const summary = await run(github, [change()])
  assert.deepEqual(summary.created, [])
  assert.deepEqual(summary.updated, [])
  assert.deepEqual(state.calls, [])
})

test('falls back to the spec PR author when the owner is not assignable', async () => {
  const { github, state } = fakeGitHub({
    assignable: ['author'],
    pulls: {
      p1: [
        { number: 5, merged_at: 'x', user: { login: 'author', type: 'User' } }
      ]
    }
  })
  await run(github, [change({ owner: 'ghost' })])
  assert.deepEqual(state.issues[0].assignees, ['author'])
})

test('update keeps ticked boxes and human evidence, survives CRLF', async () => {
  const { github, state } = fakeGitHub()
  await run(github, [change()])
  const issue = state.issues[0]
  issue.body = issue.body
    .replace('- [ ] AC-01 거부한다', '- [x] AC-01 거부한다')
    .replace('커밋 주소:', '커밋 주소: 직접 적음')
    .replace(/\n/g, '\r\n')
  const updated = change({
    managed: change().managed.replace('저장한다.', '저장하고 조회한다.')
  })
  await run(github, [updated])
  assert.match(issue.body, /- \[x\] AC-01 거부한다/)
  assert.match(issue.body, /저장하고 조회한다/)
  assert.match(issue.body, /커밋 주소: 직접 적음/)
})

test('archived change with passing checks is closed as completed with evidence', async () => {
  const { github, state } = fakeGitHub({
    pulls: {
      a1: [
        {
          number: 9,
          merged_at: 'x',
          head: { sha: 'h9' },
          user: { login: 'gray', type: 'User' }
        }
      ]
    },
    checks: { h9: passing() }
  })
  await run(github, [change()])
  const summary = await run(github, [
    change({ archived: true, archive_commit: 'a1' })
  ])
  const issue = state.issues[0]
  assert.deepEqual(summary.completed, [1])
  assert.equal(issue.state, 'closed')
  assert.equal(issue.state_reason, 'completed')
  assert.deepEqual(state.calls.at(-1), ['update', 1, 'body,state,state_reason'])
  assert.match(issue.body, /커밋 주소: https:\/\/github.com\/o\/r\/commit\/a1/)
  assert.match(issue.body, /PR: #9/)
  assert.match(issue.body, /- test-backend: success — u\/test-backend/)
  assert.match(issue.body, /- \[x\] 정상·오류 테스트 결과를 남긴다/)
})

test('archived change with a failing or missing check stays open with one pending comment', async () => {
  const { github, state } = fakeGitHub({
    checks: {
      a1: [
        ...passing(['test-backend', 'test-frontend']),
        { id: 9, name: 'test-backend', conclusion: 'failure' }
      ]
    }
  })
  await run(github, [change({ archived: true, archive_commit: 'a1' })])
  await run(github, [change({ archived: true, archive_commit: 'a1' })])
  const issue = state.issues[0]
  assert.equal(issue.state, 'open')
  assert.equal(state.comments[1].length, 1)
  assert.match(
    state.comments[1][0].body,
    /test-backend: failure, alls-green-playwright: missing/
  )
})

const NOW = Date.parse('2026-10-14T12:00:00Z')
const mergedPr = (number, sha, minutesAgo) => ({
  number,
  merged_at: new Date(NOW - minutesAgo * 60000).toISOString(),
  head: { sha },
  user: { login: 'gray', type: 'User' }
})

test('archive sync waits once for checks still running, after other Issues', async () => {
  const checks = {
    h1: [
      { id: 1, name: 'test-backend', status: 'in_progress', conclusion: null }
    ],
    h2: []
  }
  const { github, state } = fakeGitHub({
    checks,
    pulls: { a1: [mergedPr(1, 'h1', 2)], a2: [mergedPr(2, 'h2', 3)] }
  })
  let slept = 0
  await run(
    github,
    [
      change({ archived: true, archive_commit: 'a1' }),
      change({
        id: 'other',
        archived: true,
        archive_commit: 'a2',
        title: '[REQ-02] 다른 것'
      }),
      change({ id: 'fresh', title: '[REQ-03] 새 제안' })
    ],
    {
      waitForChecksMs: 90000,
      pollMs: 30000,
      now: () => NOW,
      sleep: async () => {
        // Both Issues and the new proposal's Issue exist before any wait.
        assert.equal(state.issues.length, 3)
        slept += 1
        if (slept === 2) checks.h1 = passing()
      }
    }
  )
  assert.equal(slept, 3) // one shared deadline: 90 s at 30 s each
  assert.equal(state.issues[0].state, 'closed')
  assert.equal(state.issues[1].state, 'open') // h2 checks never reported
})

test('old archives and runs without a wait budget do not wait', async () => {
  const { github, state } = fakeGitHub({
    checks: {},
    pulls: { a1: [mergedPr(1, 'h1', 60)] }
  })
  let slept = 0
  await run(github, [change({ archived: true, archive_commit: 'a1' })], {
    waitForChecksMs: 600000,
    now: () => NOW,
    sleep: async () => {
      slept += 1
    }
  })
  assert.equal(slept, 0)
  assert.equal(state.issues[0].state, 'open')
})

test('change created and archived in one merge gets an Issue that is completed', async () => {
  const { github, state } = fakeGitHub({ checks: { a1: passing() } })
  const summary = await run(github, [
    change({ archived: true, archive_commit: 'a1' })
  ])
  assert.deepEqual(summary.created, [1])
  assert.deepEqual(summary.completed, [1])
  assert.equal(state.issues[0].state_reason, 'completed')
})

test('closed Issues are never reopened or edited', async () => {
  const { github, state } = fakeGitHub({
    issues: [
      {
        number: 3,
        state: 'closed',
        body: '<!-- openspec-change: add-todo -->\nold',
        title: 'old'
      }
    ]
  })
  const summary = await run(github, [change()])
  assert.deepEqual(summary.skipped, [3])
  assert.deepEqual(state.calls, [])
})

test('vanished change is closed as not planned with a reason', async () => {
  const { github, state } = fakeGitHub({
    issues: [{ number: 4, body: '<!-- openspec-change: gone -->\nx' }]
  })
  const summary = await run(github, [])
  assert.deepEqual(summary.notPlanned, [4])
  assert.equal(state.issues[0].state_reason, 'not_planned')
  assert.match(state.comments[4][0].body, /`gone`/)
})

test('does not mass-close when OpenSpec is missing or too many vanished', async () => {
  const many = Array.from({ length: 6 }, (_, i) => ({
    number: i + 1,
    body: `<!-- openspec-change: c${i} -->`
  }))
  const first = fakeGitHub({ issues: many })
  await syncIssues({
    github: first.github,
    context,
    core,
    plan: { openspec_present: false, changes: [] },
    requiredChecks: REQUIRED
  })
  assert.ok(first.state.issues.every(i => i.state === 'open'))
  const second = fakeGitHub({ issues: many })
  await run(second.github, [])
  assert.ok(second.state.issues.every(i => i.state === 'open'))
})

test('does nothing when Issues are disabled or on another branch', async () => {
  const disabled = fakeGitHub({ hasIssues: false })
  assert.deepEqual((await run(disabled.github, [change()])).created, [])
  const other = fakeGitHub()
  await syncIssues({
    github: other.github,
    context: { ...context, ref: 'refs/heads/feature' },
    core,
    plan: { openspec_present: true, changes: [change()] },
    requiredChecks: REQUIRED
  })
  assert.equal(other.state.issues.length, 0)
})

test('ignores pull requests and Issues without the marker', async () => {
  const { github, state } = fakeGitHub({
    issues: [
      {
        number: 1,
        body: '<!-- openspec-change: add-todo -->',
        pull_request: {}
      },
      { number: 2, body: 'manual issue' }
    ]
  })
  const summary = await run(github, [change()])
  assert.deepEqual(summary.created, [3])
  assert.equal(state.issues.find(i => i.number === 2).state, 'open')
})

test('Issues opened by someone else with the marker are ignored', async () => {
  const { github, state } = fakeGitHub({
    issues: [
      {
        number: 1,
        user: { login: 'mallory' },
        body: '<!-- openspec-change: add-todo -->'
      }
    ]
  })
  const summary = await run(github, [change()])
  assert.deepEqual(summary.created, [2])
  assert.equal(state.issues[0].state, 'open')
})

test('evidence written below the automatic block survives later syncs', async () => {
  const { github, state } = fakeGitHub({
    checks: { a1: passing(['test-backend']) }
  })
  await run(github, [change({ archived: true, archive_commit: 'a1' })])
  const issue = state.issues[0]
  assert.equal(issue.state, 'open')
  issue.body += '\n스크린샷: docs/img/todo.png\n\n추가 로그는 아래와 같다.\n'
  await run(github, [change({ archived: true, archive_commit: 'a1' })])
  assert.match(
    issue.body,
    /<!-- \/openspec-sync: evidence -->\n+스크린샷: docs\/img\/todo.png\n\n추가 로그는 아래와 같다.\n$/
  )
  assert.equal(issue.body.match(/openspec-sync: evidence -->/g).length, 2)
})

test('pending comment is updated when the Issue is finally completed', async () => {
  const checks = { a1: passing(['test-backend']) }
  const { github, state } = fakeGitHub({ checks })
  await run(github, [change({ archived: true, archive_commit: 'a1' })])
  checks.a1 = passing()
  await run(github, [change({ archived: true, archive_commit: 'a1' })])
  assert.equal(state.issues[0].state_reason, 'completed')
  assert.equal(state.comments[1].length, 1)
  assert.match(state.comments[1][0].body, /완료로 닫았습니다/)
})

test('a change proposed again after its Issue was completed gets a new Issue', async () => {
  const done = {
    number: 1,
    state: 'closed',
    state_reason: 'completed',
    closed_at: '2026-10-01T00:00:00Z',
    body: '<!-- openspec-change: add-todo -->'
  }
  const { github } = fakeGitHub({ issues: [done] })
  const summary = await run(github, [
    change({ proposal_date: '2026-10-14T00:00:00+09:00' })
  ])
  assert.deepEqual(summary.created, [2])
})

test('an Issue a person closed as completed before archiving is left alone', async () => {
  const done = {
    number: 1,
    state: 'closed',
    state_reason: 'completed',
    closed_at: '2026-10-14T12:00:00Z',
    body: '<!-- openspec-change: add-todo -->'
  }
  const { github } = fakeGitHub({ issues: [done] })
  const summary = await run(github, [
    change({ proposal_date: '2026-10-13T00:00:00+09:00' })
  ])
  assert.deepEqual(summary.created, [])
  assert.deepEqual(summary.skipped, [1])
})

test('duplicate open Issues for one change are closed as not planned', async () => {
  const marker = '<!-- openspec-change: add-todo -->'
  const { github, state } = fakeGitHub({
    issues: [
      { number: 5, body: marker },
      { number: 2, body: marker }
    ]
  })
  const summary = await run(github, [change()])
  assert.deepEqual(summary.notPlanned, [5])
  assert.equal(state.issues.find(i => i.number === 2).state, 'open')
  assert.match(state.comments[5][0].body, /#2에서 관리/)
})
