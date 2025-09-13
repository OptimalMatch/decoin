# DeCoin Makefile
# Automation for common development tasks

.PHONY: help install test test-unit test-integration test-coverage clean docker-build docker-up docker-down lint format

# Default target
help:
	@echo "DeCoin Development Commands"
	@echo "============================"
	@echo "install          - Install all dependencies"
	@echo "test            - Run all tests"
	@echo "test-unit       - Run unit tests only"
	@echo "test-integration - Run integration tests only"
	@echo "test-coverage   - Run tests with coverage report"
	@echo "test-watch      - Run tests in watch mode"
	@echo "lint            - Run code linting"
	@echo "format          - Format code with black"
	@echo "clean           - Clean up temporary files"
	@echo "docker-build    - Build Docker images"
	@echo "docker-up       - Start Docker containers"
	@echo "docker-down     - Stop Docker containers"
	@echo "docker-test     - Run tests in Docker"
	@echo "run-node        - Run a single node locally"
	@echo "run-example     - Run example usage"

# Install dependencies
install:
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	. venv/bin/activate && pip install -r requirements-test.txt

# Testing targets
test:
	./run_tests.sh

test-unit:
	./run_tests.sh unit

test-integration:
	./run_tests.sh integration

test-coverage:
	./run_tests.sh coverage

test-watch:
	. venv/bin/activate && pytest-watch tests/ --clear

test-docker:
	docker build -t decoin-test -f Dockerfile.test .
	docker run --rm decoin-test

# Code quality
lint:
	. venv/bin/activate && flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503
	. venv/bin/activate && mypy src/ --ignore-missing-imports
	. venv/bin/activate && pylint src/ --disable=C0111,R0903,R0913

format:
	. venv/bin/activate && black src/ tests/
	. venv/bin/activate && isort src/ tests/

check-security:
	. venv/bin/activate && safety check
	. venv/bin/activate && bandit -r src/ -ll

# Docker commands
docker-build:
	docker compose build

docker-up:
	docker compose up -d
	@echo "Waiting for services to start..."
	@sleep 10
	@echo "Services available at:"
	@echo "  Node 1: http://localhost:10080"
	@echo "  Node 2: http://localhost:10081"
	@echo "  Node 3: http://localhost:10082"
	@echo "  Validator: http://localhost:10083"
	@echo "  Swagger UI: http://localhost:10080/docs"

docker-down:
	docker compose down

docker-clean:
	docker compose down -v
	docker system prune -f

docker-logs:
	docker compose logs -f

# Running locally
run-node:
	. venv/bin/activate && python src/node.py --config config/node1.json

run-example:
	./run_example.sh

# Development database
db-reset:
	rm -rf data/
	mkdir -p data/

# Clean up
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -delete
	find . -type d -name '.coverage' -delete
	find . -type f -name '.coverage' -delete
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info

# CI/CD
ci-test:
	pytest tests/ -v --cov=src --cov-report=xml --cov-report=term

ci-build:
	docker build -t decoin:latest .
	docker build -t decoin-test:latest -f Dockerfile.test .

# Performance testing
benchmark:
	. venv/bin/activate && python tests/performance/benchmark.py

stress-test:
	. venv/bin/activate && python tests/performance/stress_test.py

# Documentation
docs:
	. venv/bin/activate && sphinx-build -b html docs/ docs/_build

# Deployment
deploy-testnet:
	@echo "Deploying to testnet..."
	docker compose -f docker-compose.testnet.yml up -d

deploy-mainnet:
	@echo "Deploying to mainnet..."
	@echo "WARNING: This will deploy to production!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose -f docker-compose.prod.yml up -d