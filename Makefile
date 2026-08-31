.PHONY: help install install-dev test test-cov lint format typecheck clean build docs run all

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev]"

test: ## Run tests
	python3 -m unittest src.test_zloop_engine -v

test-cov: ## Run tests with coverage
	python3 -m pytest src/ --cov=src --cov-report=term-missing

lint: ## Run linter
	ruff check src/

format: ## Format code
	ruff format src/

typecheck: ## Run type checker
	mypy src/

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info .eggs/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

build: ## Build distribution packages
	python3 -m build

docs: ## Build documentation
	mkdocs build

run: ## Run demo loop
	python3 -m zloop_engine

all: lint typecheck test ## Run lint, typecheck, and test
