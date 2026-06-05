#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/riskguard}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health/}"

echo "Deploy directory: ${APP_DIR}"
echo "Deploy branch: ${DEPLOY_BRANCH}"

cd "${APP_DIR}"

echo "Fetching latest code..."
git fetch origin "${DEPLOY_BRANCH}"
git pull --ff-only origin "${DEPLOY_BRANCH}"

echo "Rebuilding and restarting Docker containers..."
docker compose up -d --build --remove-orphans

echo "Container status:"
docker compose ps

echo "Checking backend health: ${HEALTH_URL}"
curl -fsSL "${HEALTH_URL}" >/dev/null

echo "Deployment completed."
