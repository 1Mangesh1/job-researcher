.PHONY: help install dev test run lint format clean docker-build docker-up docker-down

help:
	@echo "Job Researcher - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies"
	@echo "  make dev           Install with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make run           Run FastAPI server (port 8000)"
	@echo "  make test          Run pytest suite"
	@echo "  make test-watch    Run pytest in watch mode"
	@echo "  make format        Format code with ruff"
	@echo "  make lint          Lint code with ruff"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-up     Start services with docker-compose"
	@echo "  make docker-down   Stop docker-compose services"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove __pycache__ and .pytest_cache"
	@echo ""

install:
	uv sync

dev:
	uv sync --all-extras

run:
	python -m uvicorn src.job_researcher.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

test-watch:
	pytest --watch

test-verbose:
	pytest -v

test-coverage:
	pytest --cov=src/job_researcher tests/

format:
	@command -v ruff >/dev/null 2>&1 || pip install ruff
	ruff format src tests

lint:
	@command -v ruff >/dev/null 2>&1 || pip install ruff
	ruff check src tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

docker-build:
	docker build -t job-researcher:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

venv:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install uv
	.venv/bin/uv sync --all-extras

.DEFAULT_GOAL := help
