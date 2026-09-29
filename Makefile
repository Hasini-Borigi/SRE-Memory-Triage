.PHONY: help dev seed test build up down clean

SHELL := /bin/bash
VENV_PYTHON := ./venv/bin/python3
VENV_PYTEST := ./venv/bin/pytest
NODE_PATH := /Users/balaji/.nvm/versions/node/v24.14.0/bin:$(PATH)

help:
	@echo "Available commands:"
	@echo "  make dev      - Start both backend and frontend servers locally"
	@echo "  make seed     - Seed historical incidents, runbooks, and post-mortems"
	@echo "  make test     - Run pytest test suite"
	@echo "  make build    - Build production frontend bundle"
	@echo "  make up       - Start services with docker-compose (using env_file .env)"
	@echo "  make down     - Stop docker-compose services"
	@echo "  make clean    - Remove build artifacts and temporary files"

dev:
	@echo "Starting backend and frontend in parallel..."
	@export PATH="$(NODE_PATH)"; \
	trap 'kill 0' EXIT; \
	$(VENV_PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload & \
	(cd frontend && npm run dev) & \
	wait

seed:
	@echo "Seeding persistent memory and SQLite database..."
	$(VENV_PYTHON) data/seed_data.py

test:
	@echo "Running test suite..."
	$(VENV_PYTEST) -v

build:
	@echo "Building frontend bundle..."
	@export PATH="$(NODE_PATH)"; cd frontend && npm run build

up:
	@echo "Starting Docker Compose services..."
	docker-compose up --build

down:
	@echo "Stopping Docker Compose services..."
	docker-compose down

clean:
	rm -rf .pytest_cache dist frontend/dist data/test_*.db
