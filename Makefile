.PHONY: help docs
.DEFAULT_GOAL := help

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean: ## Removing cached python compiled files
	find . -name \*pyc  | xargs  rm -fv
	find . -name \*pyo | xargs  rm -fv
	find . -name \*~  | xargs  rm -fv
	find . -name __pycache__  | xargs  rm -rfv

install: ## Install dependencies
	flit install --deps develop --symlink

lint: ## Run code linters
	make clean
	black --check django_rest_passwordreset tests
	isort --check django_rest_passwordreset tests
	flake8 django_rest_passwordreset tests
# 	mypy  ninja_jwt

fmt format: ## Run code formatters
	make clean
	black django_rest_passwordreset tests
	isort django_rest_passwordreset tests

test: ## Run tests
	make clean
	pytest .

test-cov: ## Run tests with coverage
	make clean
	pytest --cov=django_rest_passwordreset --cov-report term-missing tests
