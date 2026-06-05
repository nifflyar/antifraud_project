#!/bin/sh

# Эндпоинт для запуска бэкенда с автоматическими миграциями
# Ожидаем доступности Postgres перед запуском команд

set -e

# Функция для проверки доступности хоста и порта
wait_for_port() {
    local host="$1"
    local port="$2"
    local name="$3"
    
    echo "Waiting for $name ($host:$port)..."
    while ! nc -z "$host" "$port"; do
      sleep 1
    done
    echo "$name is up!"
}

# Ждем базу данных (хост 'postgres' берется из docker-compose)
wait_for_port "postgres" 5432 "PostgreSQL"

# Запуск миграций до актуальной версии
echo "Running database migrations..."
alembic upgrade head

# Запуск приложения
echo "Starting Uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
