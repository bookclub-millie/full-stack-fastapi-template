#!/usr/bin/env bash
# One-time GitHub settings for the CI harness (docs/ci-harness.md).
#
# Repositories created from a template get the files but not labels, rulesets,
# environments or Actions settings, so run this once in every new repository.
# Needs `gh` logged in with admin rights on the repository.
#
#   bash scripts/harness/setup-repo.sh [owner/repo]
set -euo pipefail

repo="${1:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Configuring $repo"

# GITHUB_TOKEN is read-only unless a workflow asks for more, and can't approve PRs.
gh api -X PUT "repos/$repo/actions/permissions/workflow" \
  -f default_workflow_permissions=read -F can_approve_pull_request_reviews=false

# Refuse workflows that use an action not pinned to a full commit SHA.
allowed_actions="$(gh api "repos/$repo/actions/permissions" --jq .allowed_actions)"
gh api -X PUT "repos/$repo/actions/permissions" \
  -F enabled=true -f allowed_actions="$allowed_actions" -F sha_pinning_required=true

# Workflows from any outside contributor's fork wait for a maintainer's approval.
gh api -X PUT "repos/$repo/actions/permissions/fork-pr-contributor-approval" \
  -f approval_policy=all_external_contributors

# Label used to acknowledge harness signals (the gate also creates it on first use).
gh label create harness-ack --repo "$repo" --color 0e8a16 \
  --description "Harness Gate 신호를 PR 작성자가 아닌 사람이 확인함" --force

# Environment that holds ANTHROPIC_API_KEY for the AI Review workflow.
gh api -X PUT "repos/$repo/environments/ai-review" --silent

# Default-branch ruleset: PR + 1 approval from someone other than the last pusher,
# required checks, no force push or deletion. Created or updated by name.
ruleset_id="$(gh api "repos/$repo/rulesets" --jq '.[] | select(.name == "harness") | .id')"
if [ -n "$ruleset_id" ]; then
  gh api -X PUT "repos/$repo/rulesets/$ruleset_id" --input "$here/ruleset.json" --silent
else
  gh api -X POST "repos/$repo/rulesets" --input "$here/ruleset.json" --silent
fi

cat <<NEXT
Done. To turn on AI Review, store the API key in the ai-review environment:
  gh secret set ANTHROPIC_API_KEY --env ai-review --repo $repo
NEXT
