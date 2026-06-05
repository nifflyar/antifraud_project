#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE=(docker-compose)
else
  cat >&2 <<'EOF'
Docker Compose command not found.

Run this script from your host terminal in the project folder:
  scripts/demo_status.sh

Do not run it inside the app container like:
  docker-compose exec app scripts/demo_status.sh
EOF
  exit 127
fi

"${DOCKER_COMPOSE[@]}" exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' <<'SQL'
\echo '--- uploads ---'
select status, count(*) from uploads group by status order by status;

\echo '--- core counts ---'
select 'transactions' as metric, count(*) from transactions
union all select 'passengers', count(*) from passengers
union all select 'passenger_scores', count(*) from passenger_scores
union all select 'risk_concentrations', count(*) from risk_concentrations;

\echo '--- passenger risk bands ---'
select risk_band, count(*) from passenger_scores group by risk_band order by risk_band;

\echo '--- top critical passengers ---'
select
  ps.passenger_id,
  p.fio_clean,
  ps.risk_band,
  round(ps.final_score::numeric, 1) as final_score,
  pf.refund_cnt,
  pf.suspicious_refund_pattern_cnt,
  pf.seat_blocking_flag
from passenger_scores ps
join passengers p on p.id = ps.passenger_id
left join passenger_features pf on pf.passenger_id = ps.passenger_id
order by ps.final_score desc, p.last_seen_at desc
limit 10;
SQL
