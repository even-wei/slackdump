# SlackDump Makefile
# Modern Python development workflow with uv

.PHONY: help install install-dev clean test test-watch lint format type-check \
        coverage coverage-html build publish check-all pre-commit dev-setup \
        clean-cache clean-build clean-all run-example docs

.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ Installation

install: ## Install package for production use
	@echo "$(BLUE)Installing SlackDump...$(NC)"
	uv add slackdump

install-dev: ## Install package with development dependencies
	@echo "$(BLUE)Installing development environment...$(NC)"
	uv sync --all-extras
	@echo "$(GREEN)Development environment ready!$(NC)"

dev-setup: install-dev ## Complete development setup (alias for install-dev)
	@echo "$(GREEN)✅ Development setup complete$(NC)"
	@echo "$(YELLOW)💡 Try: make test$(NC)"

##@ Development

clean: clean-cache clean-build ## Clean all generated files

clean-cache: ## Clean Python cache files
	@echo "$(YELLOW)Cleaning cache files...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

clean-build: ## Clean build artifacts
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/

clean-all: clean ## Clean everything including virtual environment
	@echo "$(YELLOW)Cleaning virtual environment...$(NC)"
	rm -rf .venv

##@ Testing

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	uv run pytest

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode (Ctrl+C to stop)...$(NC)"
	uv run pytest -f

test-verbose: ## Run tests with verbose output
	@echo "$(BLUE)Running tests (verbose)...$(NC)"
	uv run pytest -v

##@ Code Quality

lint: ## Run linter (flake8)
	@echo "$(BLUE)Running linter...$(NC)"
	uv run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	uv run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	uv run black .
	@echo "$(GREEN)✅ Code formatted$(NC)"

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	uv run black --check --diff .

type-check: ## Run type checker (mypy)
	@echo "$(BLUE)Running type checker...$(NC)"
	uv run mypy slackdump --ignore-missing-imports

##@ Coverage

coverage: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	uv run pytest --cov=slackdump --cov-report=term-missing

coverage-html: ## Generate HTML coverage report
	@echo "$(BLUE)Generating HTML coverage report...$(NC)"
	uv run pytest --cov=slackdump --cov-report=html
	@echo "$(GREEN)✅ Coverage report generated: htmlcov/index.html$(NC)"

##@ Quality Assurance

check-all: format-check lint type-check test coverage ## Run all quality checks
	@echo "$(GREEN)✅ All quality checks passed!$(NC)"

pre-commit: format lint type-check test ## Run pre-commit checks (format, lint, type-check, test)
	@echo "$(GREEN)✅ Pre-commit checks completed$(NC)"

##@ Building & Publishing

build: clean-build ## Build package for distribution
	@echo "$(BLUE)Building package...$(NC)"
	uv build
	@echo "$(GREEN)✅ Package built successfully$(NC)"
	@echo "$(YELLOW)📦 Artifacts in dist/$(NC)"

build-check: build ## Build package and check with twine
	@echo "$(BLUE)Checking built package...$(NC)"
	uv run twine check dist/*
	@echo "$(GREEN)✅ Package check passed$(NC)"

publish-test: build-check ## Publish to TestPyPI
	@echo "$(YELLOW)Publishing to TestPyPI...$(NC)"
	@echo "$(RED)⚠️  Make sure PYPI_TEST_TOKEN is set$(NC)"
	UV_PUBLISH_TOKEN=${PYPI_TEST_TOKEN} uv publish --publish-url https://test.pypi.org/legacy/

publish: build-check ## Publish to PyPI (production)
	@echo "$(YELLOW)Publishing to PyPI...$(NC)"
	@echo "$(RED)⚠️  Make sure PYPI_API_TOKEN is set$(NC)"
	@read -p "Are you sure you want to publish to PyPI? [y/N]: " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		UV_PUBLISH_TOKEN=${PYPI_API_TOKEN} uv publish; \
		echo "$(GREEN)✅ Published to PyPI$(NC)"; \
	else \
		echo "$(YELLOW)❌ Publish cancelled$(NC)"; \
	fi

##@ Usage Examples

run-example: ## Run SlackDump with example parameters (requires token/channel)
	@echo "$(BLUE)Running SlackDump example...$(NC)"
	@echo "$(YELLOW)Usage: SLACK_TOKEN=xoxb-... SLACK_CHANNEL=C... make run-example$(NC)"
	@if [ -z "$(SLACK_TOKEN)" ] || [ -z "$(SLACK_CHANNEL)" ]; then \
		echo "$(RED)❌ Please set SLACK_TOKEN and SLACK_CHANNEL environment variables$(NC)"; \
		echo "$(YELLOW)Example: SLACK_TOKEN=xoxb-... SLACK_CHANNEL=C... make run-example$(NC)"; \
		exit 1; \
	fi
	uv run python -m slackdump --token $(SLACK_TOKEN) --channel $(SLACK_CHANNEL) --limit 10

demo: ## Show SlackDump help and version
	@echo "$(BLUE)SlackDump CLI Demo:$(NC)"
	@echo "\n$(YELLOW)Version:$(NC)"
	uv run python -m slackdump --version
	@echo "\n$(YELLOW)Help:$(NC)"
	uv run python -m slackdump --help

##@ Development Utilities

show-deps: ## Show installed dependencies
	@echo "$(BLUE)Installed dependencies:$(NC)"
	uv pip list

show-env: ## Show development environment info
	@echo "$(BLUE)Environment Information:$(NC)"
	@echo "Python version: $$(uv run python --version)"
	@echo "uv version: $$(uv --version)"
	@echo "Virtual environment: $$(uv python find)"
	@echo "Project root: $$(pwd)"

update-deps: ## Update all dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	uv sync --upgrade
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

##@ Documentation

docs: ## Generate documentation (placeholder)
	@echo "$(YELLOW)📚 Documentation generation not yet implemented$(NC)"
	@echo "$(BLUE)Available documentation:$(NC)"
	@echo "  - README.md: Main project documentation"
	@echo "  - pyproject.toml: Package configuration"
	@echo "  - Makefile: This file with all commands"

##@ Information

info: show-env show-deps ## Show comprehensive environment information

version: ## Show project version
	@echo "$(BLUE)SlackDump Version:$(NC)"
	uv run python -c "import slackdump; print(slackdump.__version__)"

help: ## Display this help message
	@echo "$(BLUE)SlackDump Development Makefile$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  1. make dev-setup    # Set up development environment"
	@echo "  2. make test         # Run tests"
	@echo "  3. make pre-commit   # Run all quality checks"
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make demo            # Show CLI demo"
	@echo "  SLACK_TOKEN=xoxb-... SLACK_CHANNEL=C... make run-example"