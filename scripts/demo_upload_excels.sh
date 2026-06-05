#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_URL="${API_URL:-http://127.0.0.1:8000}"
EMAIL="${DEMO_EMAIL:-admin@example.com}"
PASSWORD="${DEMO_PASSWORD:-AdminPassword123}"
EXCEL_DIR="$ROOT_DIR/demo_data/excel"
WAIT=1
GENERATE=0
POLL_SECONDS=2
TIMEOUT_SECONDS=600

usage() {
  cat <<'EOF'
Usage:
  scripts/demo_upload_excels.sh [options]

Options:
  --dir PATH          Directory with .xlsx files. Default: demo_data/excel
  --api URL           Backend URL. Default: http://127.0.0.1:8000
  --email EMAIL       Login email. Default: admin@example.com
  --password PASS     Login password. Default: AdminPassword123
  --generate          Regenerate demo Excel files before upload
  --no-wait           Do not wait for ETL/scoring completion
  --timeout SECONDS   Wait timeout. Default: 600
  --help              Show this help

Environment alternatives:
  API_URL, DEMO_EMAIL, DEMO_PASSWORD
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir)
      EXCEL_DIR="$2"
      shift 2
      ;;
    --api)
      API_URL="$2"
      shift 2
      ;;
    --email)
      EMAIL="$2"
      shift 2
      ;;
    --password)
      PASSWORD="$2"
      shift 2
      ;;
    --generate)
      GENERATE=1
      shift
      ;;
    --no-wait)
      WAIT=0
      shift
      ;;
    --timeout)
      TIMEOUT_SECONDS="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

cd "$ROOT_DIR"

if [[ "$GENERATE" -eq 1 ]]; then
  if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    "$ROOT_DIR/.venv/bin/python" scripts/generate_demo_excels.py
  else
    python3 scripts/generate_demo_excels.py
  fi
fi

if [[ ! -d "$EXCEL_DIR" ]]; then
  echo "Excel directory not found: $EXCEL_DIR" >&2
  exit 1
fi

FILES=()
while IFS= read -r file; do
  FILES+=("$file")
done < <(find "$EXCEL_DIR" -maxdepth 1 -type f -name '*.xlsx' | sort)

if [[ "${#FILES[@]}" -eq 0 ]]; then
  echo "No .xlsx files found in $EXCEL_DIR" >&2
  exit 1
fi

COOKIE_FILE="$(mktemp)"
BODY_FILE="$(mktemp)"
IDS_FILE="$(mktemp)"
cleanup() {
  rm -f "$COOKIE_FILE" "$BODY_FILE" "$IDS_FILE"
}
trap cleanup EXIT

login_code="$(
  curl -sS -c "$COOKIE_FILE" -o "$BODY_FILE" -w '%{http_code}' \
    -X POST "$API_URL/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"
)"
if [[ "$login_code" != "200" ]]; then
  echo "Login failed: HTTP $login_code" >&2
  cat "$BODY_FILE" >&2
  exit 1
fi

echo "Uploading ${#FILES[@]} Excel files to $API_URL ..."
uploaded=0
failed=0

for file in "${FILES[@]}"; do
  code="$(
    curl -sS -b "$COOKIE_FILE" -o "$BODY_FILE" -w '%{http_code}' \
      -X POST "$API_URL/uploads/excel" \
      -F "file=@${file};type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  )"

  if [[ "$code" == "202" ]]; then
    upload_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("id",""))' "$BODY_FILE")"
    echo "$upload_id" >> "$IDS_FILE"
    uploaded=$((uploaded + 1))
    printf '[%03d/%03d] accepted upload_id=%s %s\n' "$uploaded" "${#FILES[@]}" "$upload_id" "$(basename "$file")"
  else
    failed=$((failed + 1))
    echo "UPLOAD_FAILED HTTP $code $(basename "$file")" >&2
    cat "$BODY_FILE" >&2
    echo >&2
  fi
done

echo "Upload requests finished: uploaded=$uploaded failed=$failed"
if [[ "$failed" -gt 0 ]]; then
  exit 1
fi

if [[ "$WAIT" -ne 1 ]]; then
  exit 0
fi

echo "Waiting for ETL/scoring to finish ..."
deadline=$((SECONDS + TIMEOUT_SECONDS))
while true; do
  done_count=0
  failed_count=0
  pending_count=0

  while IFS= read -r upload_id; do
    [[ -z "$upload_id" ]] && continue
    code="$(
      curl -sS -b "$COOKIE_FILE" -o "$BODY_FILE" -w '%{http_code}' \
        "$API_URL/uploads/$upload_id"
    )"
    if [[ "$code" != "200" ]]; then
      pending_count=$((pending_count + 1))
      continue
    fi

    status="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("status",""))' "$BODY_FILE")"
    case "$status" in
      DONE|done)
        done_count=$((done_count + 1))
        ;;
      FAILED|failed)
        failed_count=$((failed_count + 1))
        ;;
      *)
        pending_count=$((pending_count + 1))
        ;;
    esac
  done < "$IDS_FILE"

  printf 'status: done=%d pending=%d failed=%d\r' "$done_count" "$pending_count" "$failed_count"

  if [[ "$failed_count" -gt 0 ]]; then
    echo
    echo "Some uploads failed." >&2
    exit 1
  fi
  if [[ "$done_count" -eq "$uploaded" ]]; then
    echo
    echo "All uploads are DONE."
    break
  fi
  if [[ "$SECONDS" -ge "$deadline" ]]; then
    echo
    echo "Timed out waiting for uploads." >&2
    exit 1
  fi
  sleep "$POLL_SECONDS"
done

echo "Dashboard summary:"
curl -sS -b "$COOKIE_FILE" "$API_URL/dashboard/summary" | python3 -m json.tool
