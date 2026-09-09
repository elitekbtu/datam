COMPOSE := docker compose
PRUNE := \( -name .git -o -name node_modules -o -name .venv \) -prune -o

.DEFAULT_GOAL := help
.PHONY: help build up down reset restart logs ps shell migrate clean

help:
	@echo "make build    build both images"
	@echo "make up       build and start the stack (http://localhost)"
	@echo "make down     stop the stack, keep the database volume"
	@echo "make reset    stop the stack and drop the database volume"
	@echo "make restart  restart running services"
	@echo "make logs     follow logs"
	@echo "make ps       show service status"
	@echo "make shell    open a shell in the backend container"
	@echo "make migrate  run alembic upgrade head in the backend container"
	@echo "make clean    remove python and tooling cache files"

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v

restart:
	$(COMPOSE) restart

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

shell:
	$(COMPOSE) exec backend sh

migrate:
	$(COMPOSE) exec backend alembic -c database/alembic.ini upgrade head

clean:
	@find . $(PRUNE) -type d \( -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -exec rm -rf {} +
	@find . $(PRUNE) -type f \( -name '*.py[co]' -o -name '*.tsbuildinfo' -o -name '.DS_Store' \) -delete
	@echo "cleaned cache files"
