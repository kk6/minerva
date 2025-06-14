# Minerva Development Makefile
# Provides unified interface for common development commands

.PHONY: help install setup-dev test test-fast test-slow test-cov lint type-check format dev clean check-all check-fast fix-whitespace

# Default target
.DEFAULT_GOAL := help

# Colors for help output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Environment check
UV_CHECK := $(shell command -v uv 2> /dev/null)
ifndef UV_CHECK
$(error "uv is not installed. Please install uv first: https://docs.astral.sh/uv/")
endif

help: ## Display this help message
	@echo "$(BLUE)Minerva Development Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)Development Environment:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		grep -E "(install|setup-dev|clean)" | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Testing:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		grep -E "^test" | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Quality Checks:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		grep -E "(lint|type-check|format|check-fast|check-all|fix-whitespace|pre-commit)" | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Development Tools:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		grep -E "(dev)" | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(RESET) %s\n", $$1, $$2}'

install: ## Install project dependencies
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	uv pip install -e .
	uv sync --group dev
	@echo "$(GREEN)Dependencies installed successfully$(RESET)"

setup-dev: install ## Set up complete development environment
	@echo "$(BLUE)Setting up development environment...$(RESET)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Warning: .env file not found. Create one with OBSIDIAN_VAULT_ROOT and DEFAULT_VAULT$(RESET)"; \
	fi
	uv run pre-commit install
	@echo "$(GREEN)Development environment setup complete$(RESET)"

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(RESET)"
	PYTHONPATH=src uv run pytest

test-fast: ## Run fast tests only (excludes slow integration tests)
	@echo "$(BLUE)Running fast tests (excluding slow tests)...$(RESET)"
	PYTHONPATH=src uv run pytest -m "not slow"
	@echo "$(GREEN)Fast tests completed! Use 'make test' for full test suite.$(RESET)"

test-slow: ## Run slow integration tests only
	@echo "$(BLUE)Running slow integration tests...$(RESET)"
	PYTHONPATH=src uv run pytest -m "slow"
	@echo "$(GREEN)Slow tests completed!$(RESET)"

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	PYTHONPATH=src uv run pytest --cov=minerva --cov-report=xml --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated in htmlcov/$(RESET)"

lint: ## Run code linting with ruff
	@echo "$(BLUE)Running linting...$(RESET)"
	uv run ruff check

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checking...$(RESET)"
	PYTHONPATH=src uv run mypy src tests

format: ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(RESET)"
	uv run ruff format

dev: ## Start MCP inspector for development
	@echo "$(BLUE)Starting MCP inspector...$(RESET)"
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file required for MCP inspector$(RESET)"; \
		exit 1; \
	fi
	PYTHONPATH=src uv run mcp dev src/minerva/server.py:mcp

clean: ## Clean build artifacts and cache
	@echo "$(BLUE)Cleaning build artifacts...$(RESET)"
	/usr/bin/find . -type f -name "*.pyc" -delete
	/usr/bin/find . -type d -name "__pycache__" -delete
	/usr/bin/find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/
	@echo "$(GREEN)Clean complete$(RESET)"

fix-whitespace: ## Fix trailing whitespace in source files
	@echo "$(BLUE)Fixing trailing whitespace...$(RESET)"
	@echo "$(YELLOW)Using pre-commit trailing-whitespace hook for safe whitespace removal$(RESET)"
	PYTHONPATH=src uv run pre-commit run trailing-whitespace --all-files || true
	@echo "$(GREEN)Trailing whitespace fixed$(RESET)"

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(RESET)"
	PYTHONPATH=src uv run pre-commit run --all-files
	@echo "$(GREEN)Pre-commit checks passed!$(RESET)"

check-fast: lint type-check test-fast ## Run fast quality checks (excludes slow tests)
	@echo "$(GREEN)Fast quality checks passed!$(RESET)"

check-all: lint type-check test ## Run comprehensive quality checks
	@echo "$(GREEN)All quality checks passed!$(RESET)"
