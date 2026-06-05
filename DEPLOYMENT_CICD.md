# RiskGuard CI/CD

## Как это работает

После каждого `git push` в ветку `main` GitHub Actions:

1. Проверяет Python-код через `compileall`.
2. Собирает frontend через `npm run build`.
3. Если проверки прошли, подключается к Ubuntu-серверу по SSH.
4. На сервере заходит в папку проекта, делает `git pull --ff-only`.
5. Пересобирает и перезапускает контейнеры через `docker compose up -d --build --remove-orphans`.
6. Проверяет health endpoint backend.

## Что нужно один раз настроить на сервере

Проект должен быть уже склонирован на сервер, например:

```bash
/opt/riskguard
```

В этой папке должны лежать серверные файлы:

```bash
.env
config.docker.yaml
```

Проверка ручного деплоя:

```bash
cd /opt/riskguard
bash scripts/deploy_pull_restart.sh
```

## SSH-ключ для GitHub Actions

На сервере создай отдельный deploy key:

```bash
ssh-keygen -t ed25519 -C "riskguard-github-actions"
cat ~/.ssh/id_ed25519.pub
```

Публичный ключ добавь в `~/.ssh/authorized_keys` пользователя, под которым деплоишь.

Приватный ключ добавь в GitHub:

`Repository -> Settings -> Secrets and variables -> Actions -> New repository secret`

Обязательные secrets:

```text
SERVER_HOST=IP_СЕРВЕРА
SERVER_USER=ubuntu
SERVER_SSH_KEY=приватный SSH ключ
```

Опциональные secrets:

```text
SERVER_PORT=22
DEPLOY_PATH=/opt/riskguard
DEPLOY_BRANCH=main
HEALTH_URL=http://localhost:8000/health/
```

## Важные условия

- На сервере должен работать Docker Compose plugin: `docker compose version`.
- Пользователь `SERVER_USER` должен иметь право запускать Docker без `sudo`.
- Серверный репозиторий не должен иметь незакоммиченных изменений. Деплой использует `git pull --ff-only`, чтобы не затирать локальные правки.
- `.env` нельзя коммитить в GitHub. Он должен оставаться только на сервере.
