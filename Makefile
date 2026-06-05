.PHONY: help docker-build docker-up docker-down docker-logs docker-clean docker-shell \
        docker-migrate docker-test docker-lint docker-format db-init db-shell \
        app-shell env-setup rebuild dev prod

help:
	@echo "Antifrode Backend - Docker Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup:"
	@echo "  make env-setup        - Copy .env.example to .env"
	@echo ""
	@echo "Docker Management:"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-up        - Start all containers"
	@echo "  make docker-down      - Stop all containers"
	@echo "  make docker-stop      - Stop containers without removing"
	@echo "  make docker-restart   - Restart all containers"
	@echo "  make docker-logs      - View container logs"
	@echo "  make docker-clean     - Remove all containers and volumes"
	@echo "  make rebuild          - Rebuild image and restart"
	@echo ""
	@echo "Access Services:"
	@echo "  make app-shell        - Access application shell"
	@echo "  make db-shell         - Access PostgreSQL shell"
	@echo "  make app-logs         - View application logs"
	@echo "  make db-logs          - View database logs"
	@echo ""
	@echo "Database:"
	@echo "  make db-init          - Initialize database"
	@echo "  make db-migrate       - Run migrations"
	@echo "  make db-rollback      - Rollback one migration"
	@echo ""
	@echo "Development:"
	@echo "  make dev              - Start development environment"
	@echo "  make prod             - Start production environment"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make docker-test      - Run tests"
	@echo "  make docker-lint      - Run linting"
	@echo "  make docker-format    - Format code"

# Setup
env-setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env file"; \
	else \
		echo "✗ .env already exists"; \
	fi

# Docker Image
docker-build:
	@echo "Building Docker image..."
	docker-compose build
	@echo "✓ Build complete"

docker-rebuild: docker-clean docker-build docker-up

# Container Management
docker-up:
	@echo "Starting containers..."
	docker-compose up -d
	@echo "✓ Containers started"
	@echo ""
	@echo "Services:"
	@echo "  API:        http://localhost:8000"
	@echo "  Database:   localhost:5432"
	@echo "  Health:     curl http://localhost:8000/health/"

docker-down:
	@echo "Stopping containers..."
	docker-compose down
	@echo "✓ Containers stopped"

docker-stop:
	@echo "Stopping containers (keeping volumes)..."
	docker-compose stop
	@echo "✓ Containers stopped"

docker-restart:
	@echo "Restarting containers..."
	docker-compose restart
	@echo "✓ Containers restarted"

docker-ps:
	docker-compose ps

docker-logs:
	docker-compose logs -f

app-logs:
	docker-compose logs -f app

db-logs:
	docker-compose logs -f postgres

# Access Services
app-shell:
	docker-compose exec app sh

db-shell:
	docker-compose exec postgres psql -U antifrode -d antifrode_db

# Database
db-init:
	@echo "Initializing database..."
	docker-compose exec app alembic upgrade head
	@echo "✓ Database initialized"

db-migrate:
	@echo "Running migrations..."
	docker-compose exec app alembic upgrade head
	@echo "✓ Migrations applied"

db-new-migration:
	@read -p "Enter migration description: " desc; \
	docker-compose exec app alembic revision --autogenerate -m "$$desc"

db-rollback:
	@echo "Rolling back one migration..."
	docker-compose exec app alembic downgrade -1
	@echo "✓ Migration rolled back"

db-current:
	docker-compose exec app alembic current

db-history:
	docker-compose exec app alembic history --verbose

# Cleanup
docker-clean:
	@echo "Removing containers and volumes..."
	docker-compose down -v
	@echo "✓ Cleanup complete"

docker-prune:
	@echo "Removing dangling Docker resources..."
	docker system prune -a --volumes
	@echo "✓ System pruned"

# Development
dev:
	@echo "Starting development environment..."
	docker-compose -f docker-compose.yml up
	@echo ""
	@echo "Development environment started!"

prod:
	@echo "Starting production environment..."
	docker-compose up -d
	@echo ""
	@echo "✓ Production environment started"
	@echo "API: http://localhost:8000"

# Build and Start
rebuild: docker-build docker-up

# Testing & Quality
docker-test:
	docker-compose exec app pytest

docker-lint:
	docker-compose exec app pylint app/

docker-format:
	docker-compose exec app black app/
	docker-compose exec app isort app/

# Utility
health-check:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health/ | python -m json.tool
	@echo ""
	@echo "✓ API is healthy"

version:
	@docker -v
	@docker-compose -v

# Info
info:
	@echo "Antifrode Backend - System Info"
	@echo "================================"
	@echo ""
	@echo "Docker:"
	@echo "  Version: $$(docker -v)"
	@echo "  Compose: $$(docker-compose -v)"
	@echo ""
	@echo "Containers:"
	@echo "$$(docker-compose ps --services)"
	@echo ""
	@echo "Volumes:"
	@echo "$$(docker-compose config --services | xargs -I {} docker-compose config --format json | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | sort -u)"

.DEFAULT_GOAL := help
