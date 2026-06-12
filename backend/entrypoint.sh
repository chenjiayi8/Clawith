#!/bin/bash
# Docker entrypoint: run DB migrations, then start the app.
# Order matters:
#   1. alembic upgrade head — apply all migrations (creates tables + schema changes)
#   2. verify declared Python dependencies are importable (catches stale images)
#   3. uvicorn — starts the FastAPI app

set -e

# --- Permission fixing and privilege dropping ---
if [ "$(id -u)" = '0' ]; then
    echo "[entrypoint] Detected root user, fixing permissions..."
    chown -R clawith:clawith ${AGENT_DATA_DIR}

    # Add clawith to docker group (GID from mounted socket) for workspace container management
    DOCKER_SOCK_GID=$(stat -c '%g' /var/run/docker.sock 2>/dev/null || true)
    if [ -n "$DOCKER_SOCK_GID" ] && [ "$DOCKER_SOCK_GID" != "0" ]; then
        echo "[entrypoint] Adding clawith to docker socket group (GID=$DOCKER_SOCK_GID)..."
        groupadd -g "$DOCKER_SOCK_GID" -o docker 2>/dev/null || true
        usermod -aG docker clawith 2>/dev/null || true
    fi

    echo "[entrypoint] Dropping privileges to 'clawith' and re-executing..."
    exec gosu clawith /bin/bash "$0" "$@"
fi
# -------------------------------------------------------

echo "[entrypoint] Step 1: Running alembic migrations..."
# Run all migrations to ensure database schema is up to date.
# Capture exit code explicitly — do NOT let a migration failure go unnoticed.
set +e
ALEMBIC_OUTPUT=$(alembic upgrade head 2>&1)
ALEMBIC_EXIT=$?
set -e

if [ $ALEMBIC_EXIT -ne 0 ]; then
    echo ""
    echo "========================================================================"
    echo "[entrypoint] WARNING: Alembic migration FAILED (exit code $ALEMBIC_EXIT)"
    echo "========================================================================"
    echo ""
    echo "$ALEMBIC_OUTPUT"
    echo ""
    echo "------------------------------------------------------------------------"
    echo "  The database schema may be INCOMPLETE. Some features will NOT work."
    echo "  Common causes:"
    echo "    - Migration cycle detected (pull latest code to fix)"
    echo "    - Database connection issue"
    echo "    - Incompatible migration state"
    echo ""
    echo "  To fix: pull the latest code and restart the backend."
    echo "    Docker:  git pull && docker compose restart backend"
    echo "    Source:  git pull && alembic upgrade head"
    echo "------------------------------------------------------------------------"
    echo ""
    exit $ALEMBIC_EXIT
else
    echo "[entrypoint] Alembic migrations completed successfully."
fi

echo "[entrypoint] Step 1.5: Verifying Python dependencies..."
python3 << 'PYEOF'
import sys, tomllib

# Import the shared mapping module (same source as main.py _check_dependencies)
sys.path.insert(0, "/app")
from app.dep_mapping import MAPPING

try:
    with open("/app/pyproject.toml", "rb") as f:
        data = tomllib.load(f)
except FileNotFoundError:
    print("[entrypoint] WARNING: pyproject.toml not found, skipping dependency verification")
    sys.exit(0)

deps = data.get("project", {}).get("dependencies", [])
failed = []

for dep_line in deps:
    # Extract base package name: strip version specifiers, extras, and whitespace
    name = dep_line.split("[")[0].split(">")[0].split("=")[0].split("!=")[0].split("<")[0].split("~")[0].strip()
    import_name = MAPPING.get(name, name.replace("-", "_"))
    try:
        __import__(import_name)
    except ImportError:
        failed.append(f"{name} (import as '{import_name}')")

if failed:
    print(f"[entrypoint] CRITICAL: Missing {len(failed)} declared dependencies:")
    for f in failed:
        print(f"  - {f}")
    print("[entrypoint] The container image is stale. Rebuild with: docker compose build --no-cache")
    sys.exit(1)

print(f"[entrypoint] OK: All {len(deps)} declared dependencies verified")
PYEOF

echo "[entrypoint] Step 2: Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
