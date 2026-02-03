.PHONY: help install dev run test lint format clean docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  install      - Install dependencies"
	@echo "  dev          - Run development server"
	@echo "  run          - Run production server"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linter"
	@echo "  format       - Format code"
	@echo "  clean        - Clean cache files"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"

install:
	pip install -r requirements.txt

dev:
	python scripts/run_dev.py

run:
	uvicorn src.main:app --host 0.0.0.0 --port 8000

test:
	pytest -v --cov=src --cov-report=term-missing

lint:
	ruff check src/
	mypy src/

format:
	black src/
	ruff check src/ --fix

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

docker-build:
	docker build -t dip-studio:latest .

docker-run:
	docker run -p 8000:8000 --env-file .env dip-studio:latest

init-db:
	python scripts/init_db.py
