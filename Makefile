.PHONY: help install dev test run api ui start stop restart status logs lint format clean docker-build docker-up docker-down

# ---- Config -----------------------------------------------------------------

PORT_API ?= 8000
PORT_UI  ?= 3000
UI_DIR    = frontend/docs
LOG_DIR   = /tmp/jr

# ---- Help -------------------------------------------------------------------

help:
	@echo "Job Researcher — dev commands"
	@echo ""
	@echo "Run locally:"
	@echo "  make start         Run backend (:$(PORT_API)) + UI (:$(PORT_UI)) together, Ctrl+C kills both"
	@echo "  make api           Backend only"
	@echo "  make ui            UI only"
	@echo "  make stop          Kill anything on :$(PORT_API) and :$(PORT_UI)"
	@echo "  make restart       stop + start"
	@echo "  make status        Show what's on the dev ports"
	@echo "  make logs          Tail the detached logs (if started with nohup)"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies (uv sync)"
	@echo "  make dev           Install with dev extras"
	@echo "  make venv          Create .venv and install"
	@echo ""
	@echo "Quality:"
	@echo "  make test          Run pytest"
	@echo "  make test-watch    pytest in watch mode"
	@echo "  make format        ruff format"
	@echo "  make lint          ruff check"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build | docker-up | docker-down | docker-logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove __pycache__ / .pytest_cache / .ruff_cache"

# ---- Setup ------------------------------------------------------------------

install:
	uv sync

dev:
	uv sync --all-extras

venv:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install uv
	.venv/bin/uv sync --all-extras

# ---- Run --------------------------------------------------------------------

# Backend only
api run:
	python -m uvicorn src.job_researcher.main:app --reload --host 0.0.0.0 --port $(PORT_API)

# UI only (static)
ui:
	@cd $(UI_DIR) && python3 -m http.server $(PORT_UI)

# Both, concurrently. Ctrl+C kills both via signal-to-process-group.
start: _check-ports
	@echo "▸ Starting backend (http://localhost:$(PORT_API)) and UI (http://localhost:$(PORT_UI))"
	@echo "  Ctrl+C to stop both."
	@trap 'echo ""; echo "▸ Shutting down..."; kill 0 2>/dev/null; exit 0' EXIT INT TERM; \
	 ( python -m uvicorn src.job_researcher.main:app --reload --host 0.0.0.0 --port $(PORT_API) 2>&1 | sed -u 's/^/\x1b[36m[api]\x1b[0m /' ) & \
	 ( cd $(UI_DIR) && python3 -m http.server $(PORT_UI) 2>&1 | sed -u 's/^/\x1b[33m[ui] \x1b[0m /' ) & \
	 wait

stop:
	@echo "▸ Killing anything on :$(PORT_API) and :$(PORT_UI)..."
	-@pids="$$(lsof -ti:$(PORT_API) 2>/dev/null)"; [ -n "$$pids" ] && kill $$pids 2>/dev/null && echo "  killed $$pids on :$(PORT_API)" || echo "  :$(PORT_API) already free"
	-@pids="$$(lsof -ti:$(PORT_UI)  2>/dev/null)"; [ -n "$$pids" ] && kill $$pids 2>/dev/null && echo "  killed $$pids on :$(PORT_UI)"  || echo "  :$(PORT_UI) already free"

restart: stop
	@sleep 1
	@$(MAKE) start

status:
	@echo "API  :$(PORT_API) →"; \
	 out="$$(lsof -i:$(PORT_API) 2>/dev/null | tail -n +2)"; \
	 [ -n "$$out" ] && echo "$$out" || echo "  (free)"
	@echo "UI   :$(PORT_UI) →"; \
	 out="$$(lsof -i:$(PORT_UI) 2>/dev/null | tail -n +2)"; \
	 [ -n "$$out" ] && echo "$$out" || echo "  (free)"

logs:
	@[ -d $(LOG_DIR) ] || mkdir -p $(LOG_DIR)
	@tail -F $(LOG_DIR)/api.log $(LOG_DIR)/ui.log 2>/dev/null || echo "no logs at $(LOG_DIR)/"

# Start detached (for when you want the terminal back). Logs go to /tmp/jr/.
start-bg: _check-ports
	@mkdir -p $(LOG_DIR)
	@nohup python -m uvicorn src.job_researcher.main:app --reload --host 0.0.0.0 --port $(PORT_API) >$(LOG_DIR)/api.log 2>&1 & \
	 echo $$! > $(LOG_DIR)/api.pid
	@cd $(UI_DIR) && nohup python3 -m http.server $(PORT_UI) >$(LOG_DIR)/ui.log 2>&1 & \
	 echo $$! > $(LOG_DIR)/ui.pid
	@echo "▸ Detached. Logs: $(LOG_DIR)/api.log $(LOG_DIR)/ui.log"
	@echo "  http://localhost:$(PORT_API)  (API + /docs)"
	@echo "  http://localhost:$(PORT_UI)   (UI)"
	@echo "  make stop    # to kill both"

# Private: fail fast if ports are busy
_check-ports:
	@if lsof -ti:$(PORT_API) >/dev/null 2>&1; then \
	  echo "✗ port $(PORT_API) is busy. 'make stop' to free it, or set PORT_API=..."; exit 1; fi
	@if lsof -ti:$(PORT_UI)  >/dev/null 2>&1; then \
	  echo "✗ port $(PORT_UI) is busy. 'make stop' to free it, or set PORT_UI=..."; exit 1; fi

# ---- Test / Quality ---------------------------------------------------------

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

# ---- Clean ------------------------------------------------------------------

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# ---- Docker -----------------------------------------------------------------

docker-build:
	docker build -t job-researcher:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

.DEFAULT_GOAL := help
