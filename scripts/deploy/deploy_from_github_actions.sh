#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <commit-sha> [repo-root]" >&2
}

print_diagnostics() {
  local scope="${1:-backend}"
  docker compose ps >&2 || true
  if [[ "$scope" == "all" ]]; then
    docker compose logs --tail=200 >&2 || true
  else
    docker compose logs --tail=200 backend >&2 || true
  fi
}

fail_with_diagnostics() {
  local message="$1"
  local scope="${2:-backend}"
  echo "$message" >&2
  print_diagnostics "$scope"
  exit 1
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 1
fi

commit_sha="$1"
repo_root="${2:-/opt/clawith}"
max_attempts=36
sleep_seconds=5

if [[ ! -d "$repo_root/.git" && ! -f "$repo_root/.git" ]]; then
  echo "Repository root does not look like a git checkout: $repo_root" >&2
  exit 1
fi

cd "$repo_root"

echo "Deploying commit $commit_sha in $repo_root"

git fetch origin main
git checkout -f main

git reset --hard "$commit_sha"
git clean -ffd \
  -e .env \
  -e backend/agent_data/ \
  -e backend/data/ \
  -e data/ \
  -e ss-nodes.json
git clean -ffdX \
  -e .env \
  -e backend/agent_data/ \
  -e backend/data/ \
  -e data/ \
  -e ss-nodes.json

if ! docker compose up -d --build; then
  fail_with_diagnostics "Deployment failed: docker compose up -d --build exited non-zero" all
fi

backend_container_id=""
last_state="unknown"

for attempt in $(seq 1 "$max_attempts"); do
  backend_container_id="$(docker compose ps -q backend)"

  if [[ -n "$backend_container_id" ]]; then
    last_state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$backend_container_id" 2>/dev/null || echo unknown)"
    echo "Attempt $attempt/$max_attempts: backend health=$last_state"

    if [[ "$last_state" == "healthy" ]]; then
      if ! docker compose exec -T backend curl -fsS http://localhost:8000/api/health; then
        fail_with_diagnostics "Deployment failed: backend health endpoint check failed for commit $commit_sha"
      fi
      echo
      echo "Deployment health check passed for commit $commit_sha"
      exit 0
    fi
  else
    echo "Attempt $attempt/$max_attempts: backend container not created yet"
  fi

  sleep "$sleep_seconds"
done

fail_with_diagnostics "Deployment failed: backend did not become ready after $max_attempts attempts (last state: $last_state)"
