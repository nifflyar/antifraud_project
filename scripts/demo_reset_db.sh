#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
YES=0
DOCKER_COMPOSE=()

for arg in "$@"; do
  case "$arg" in
    --yes|-y)
      YES=1
      ;;
    --help|-h)
      cat <<'EOF'
Usage:
  scripts/demo_reset_db.sh [--yes]

Clears demo/business data from the local Docker Postgres database while keeping users.
Tables cleared: uploads, transactions, passengers, passenger_features,
passenger_scores, scoring_jobs, risk_concentrations, audit_logs, refresh_sessions.
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

cd "$ROOT_DIR"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE=(docker-compose)
else
  cat >&2 <<'EOF'
Docker Compose command not found.

Run this script from your host terminal in the project folder:
  scripts/demo_reset_db.sh

Do not run it inside the app container like:
  docker-compose exec app scripts/demo_reset_db.sh
EOF
  exit 127
fi

if [[ "$YES" -ne 1 ]]; then
  echo "This will DELETE demo/business data from the local database."
  echo "Users are preserved, so admin@example.com will still work."
  printf 'Type RESET to continue: '
  read -r answer
  if [[ "$answer" != "RESET" ]]; then
    echo "Aborted."
    exit 1
  fi
fi

"${DOCKER_COMPOSE[@]}" exec -T postgres sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' <<'SQL'
TRUNCATE TABLE
  refresh_sessions,
  audit_logs,
  risk_concentrations,
  scoring_jobs,
  passenger_scores,
  passenger_features,
  transactions,
  passengers,
  uploads
RESTART IDENTITY CASCADE;
SQL

echo "Database demo data cleared."
"${DOCKER_COMPOSE[@]}" exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
select '\''uploads'\'' as table_name, count(*) from uploads
union all select '\''transactions'\'', count(*) from transactions
union all select '\''passengers'\'', count(*) from passengers
union all select '\''passenger_scores'\'', count(*) from passenger_scores;
"'
