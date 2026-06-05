# Presentation Workflow

## 1. Start The App

```bash
docker compose up -d
```

If your machine uses the old Compose binary, use:

```bash
docker-compose up -d
```

Open:

```text
http://localhost:3000/login
```

Demo login:

```text
admin@example.com
AdminPassword123
```

## 2. Optional Clean Start

This deletes uploaded files metadata, transactions, passengers, scores, scoring jobs,
risk concentrations, audit logs and sessions. Users are preserved.

Interactive safe mode:

```bash
scripts/demo_reset_db.sh
```

Run this from the host terminal in the project folder. Do not run it through
`docker-compose exec app ...`; the app container does not have Docker CLI.

Fast mode for rehearsals:

```bash
scripts/demo_reset_db.sh --yes
```

## 3. Generate Demo Excel Files

```bash
.venv/bin/python scripts/generate_demo_excels.py
```

Files are created in:

```text
demo_data/excel/
```

Manifest:

```text
demo_data/demo_manifest.csv
```

## 4. Upload Files Visually Through The UI

Use this during the presentation if you want to show the workflow:

1. Go to `Загрузка и скоринг`.
2. Click the upload area.
3. Select all files in `demo_data/excel/`.
4. Confirm selection.
5. The UI uploads files one by one and backend starts ETL/scoring.
6. Wait until uploads show `DONE`.
7. Go to `Дашборд`, `Пассажиры`, `Операции`.

Expected after full demo pack:

```text
critical passengers > 0
high passengers > 0
normal refund control days have 0 suspicious operations
```

## 5. Upload All Files Fast Through CLI

Use this before the presentation or when you need a quick reset/reload:

```bash
scripts/demo_upload_excels.sh --generate
```

The script logs in, uploads all `.xlsx` files from `demo_data/excel/`,
waits for ETL/scoring to finish, and prints dashboard summary.

Custom backend URL:

```bash
scripts/demo_upload_excels.sh --api http://127.0.0.1:8000
```

## 6. Check Result

```bash
scripts/demo_status.sh
```

Useful screens for the story:

```text
Дашборд -> доля suspicious operations and trend
Пассажиры -> Critical
Операции -> sort by Score descending
Reports -> export suspicious operations / passengers
```

## 7. Recommended Demo Story

1. Start from empty DB or explain that the system is clean.
2. Upload several files visually.
3. For full data volume, run CLI upload or select all Excel files in UI.
4. Show dashboard percentages and trend.
5. Open `Пассажиры -> Critical`.
6. Open one passenger profile and explain the rule-based critical reasons.
7. Open `Операции`, sort by score descending, and show operation-level reasons.
8. Export an Excel report from `Reports`.
