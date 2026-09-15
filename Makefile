.PHONY: help test test-domains test-kernel lint type test-unit audit diagnose clean hygiene

help: ## Mostrar este mensaje
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN{FS=":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

test: ## Ejecutar todos los tests
	python -m pytest tests/ -q

test-domains: ## Tests de dominio (incluye cleanup scripts)
	bash scripts/cleanup_repo.sh
	python -m pytest tests/domains/ tests/kernel/ tests/security/ -q

test-kernel: ## Tests del kernel (invariantes)
	python -m pytest tests/kernel/ tests/bugs/ -q

lint: ## Lint con ruff
	ruff check src/ tests/

type: ## Type check con mypy
	mypy src/ --ignore-missing-imports

audit: ## Verificar higiene del repo (12 checks)
	bash scripts/audit.sh

diagnose: ## Diagnóstico de entorno
	bash scripts/diagnose.sh

clean: ## Limpiar caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache/ .ruff_cache/ 2>/dev/null || true

hygiene: ## Ejecutar higiene del repo
	bash scripts/cleanup_repo.sh
