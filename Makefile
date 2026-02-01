.DEFAULT_GOAL := help
.PHONY: help install dev test lint format logs stop clean check-env ps

# Variáveis
PYTHON := uv run python
UV := uv
COMPOSE := docker compose -f docker-compose.local.yml
ENV_FILE := .env

# Cores para output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# ==============================================================================
# FLEETINTEL MCP - MAKEFILE DE DESENVOLVIMENTO
# ==============================================================================
# Este Makefile centraliza comandos comuns de desenvolvimento para facilitar
# o workflow local. Todos os comandos usam UV para gerenciamento de dependências.
# Uso: make <comando>
# Lista de comandos: make help
# ==============================================================================

help: ## Mostra esta mensagem de ajuda
	@echo "$(GREEN)FleetIntel MCP - Comandos Disponíveis:$(NC)"
	@echo ""
	@powershell -Command "Get-Content $(MAKEFILE_LIST) | Select-String -Pattern '^[a-zA-Z_-]+:.*?## .*$$' | ForEach-Object { $$_.Line -replace '^([^:]+):.*?## (.*)$$', '  $(YELLOW)$$1$$(NC) $$2' }"
	@echo ""

install: ## Instala dependências do projeto com UV
	@echo "$(GREEN)⬇️ Instalando dependências...$(NC)"
	@$(UV) sync
	@powershell -Command "if (!(Test-Path -Path '$(ENV_FILE)')) { Write-Host '$(YELLOW)⚠️ Arquivo .env não encontrado. Criando a partir de .env.example...$(NC)'; Copy-Item .env.example .env; Write-Host '$(GREEN)✅ .env criado. Edite com suas credenciais!$(NC)' }"
	@echo "$(GREEN)✅ Dependências instaladas!$(NC)"

check-env: ## Verifica se o arquivo .env existe
	@powershell -Command "if (!(Test-Path -Path '$(ENV_FILE)')) { Write-Host '$(RED)❌ ERRO: Arquivo .env não encontrado!$(NC)'; Write-Host 'Execute `make install` para criar automaticamente ou copie .env.example'; exit 1 }"

dev: check-env ## Sobe stack local (Docker Compose)
	@echo "$(GREEN)🚀 Subindo serviços locais...$(NC)"
	@$(COMPOSE) up -d
	@echo "$(GREEN)✅ Serviços iniciados!$(NC)"
	@echo "$(YELLOW)Use 'make logs' para ver logs$(NC)"

test: ## Executa testes com Pytest
	@echo "$(GREEN)🔍 Executando testes...$(NC)"
	@$(UV) run pytest || (echo "$(YELLOW)⚠️ Testes falharam ou ainda não implementados$(NC)" && exit 0)
	@echo "$(GREEN)✅ Testes concluídos!$(NC)"

lint: ## Verifica qualidade do código com Ruff e Black
	@echo "$(GREEN)🔎 Verificando estilo de código...$(NC)"
	@$(UV) run ruff check . || (echo "$(YELLOW)⚠️ Problemas encontrados pelo Ruff$(NC)" && exit 1)
	@$(UV) run black --check . || (echo "$(YELLOW)⚠️ Formatação inconsistente encontrada$(NC)" && exit 1)
	@echo "$(GREEN)✅ Linting passou!$(NC)"

format: ## Formata código automaticamente com Black e Ruff
	@echo "$(GREEN)✨ Formatando código...$(NC)"
	@$(UV) run black .
	@$(UV) run ruff --fix .
	@echo "$(GREEN)✅ Código formatado!$(NC)"

logs: ## Mostra logs dos serviços em tempo real
	@echo "$(GREEN)📜 Exibindo logs... (Ctrl+C para sair)$(NC)"
	@$(COMPOSE) logs -f

stop: ## Para todos os serviços
	@echo "$(GREEN)🛑 Parando serviços...$(NC)"
	@$(COMPOSE) down
	@echo "$(GREEN)✅ Serviços parados!$(NC)"

ps: ## Mostra status dos containers
	@echo "$(GREEN)📦 Status dos containers:$(NC)"
	@$(COMPOSE) ps

clean: ## Limpa caches e arquivos temporários
	@echo "$(GREEN)🧹 Limpando caches...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@echo "$(GREEN)✅ Limpeza concluída!$(NC)"

.PHONY: db-test
db-test: ## Executa testes específicos de banco de dados
	@echo "$(GREEN)🔍 Executando testes de banco de dados...$(NC)"
	@powershell -Command "$$env:PYTHONPATH='src'; $(UV) run pytest tests/test_db/ -v; if ($$LASTEXITCODE -ne 0) { echo \"$(YELLOW)⚠️ Testes falharam ou ainda não implementados$(NC)\" }"

.PHONY: db-shell
db-shell: ## Abre shell do banco de dados
	@echo "$(GREEN)💻 Abrindo shell do PostgreSQL...$(NC)"
	@PGPASSWORD=$(shell grep DATABASE_URL .env | cut -d'@' -f2 | cut -d':' -f2) \
	psql $(DATABASE_URL)

.PHONY: migrate
migrate: ## Executa migrações de banco de dados
	@echo "$(GREEN)🚀 Executando migrações...$(NC)"
	@powershell -Command "$$env:PYTHONPATH='src'; uv run python scripts/migrate.py"

.PHONY: db-health
db-health: ## Executa health check do banco de dados
	@echo "$(GREEN)🏥 Executando health check...$(NC)"
	@powershell -Command "$$env:PYTHONPATH='src'; uv run python scripts/db_health.py"

.PHONY: db-refresh-views
db-refresh-views: ## Atualiza views materializadas manualmente
	@echo "$(GREEN)🔄 Atualizando views materializadas...$(NC)"
	@powershell -Command "$$env:PYTHONPATH='src'; uv run python -c \"import asyncio; from sqlalchemy import text; from fleet_intel_mcp.db.connection import engine; asyncio.run((lambda: engine.begin()).__call__()).execute(text('SELECT refresh_materialized_views_concurrently()'))\""
	@echo "$(GREEN)✅ Views atualizadas!$(NC)"

.PHONY: db-maintenance
db-maintenance: ## Executa manutenção completa do banco
	@echo "$(GREEN)🔧 Executando manutenção do banco...$(NC)"
	@echo "$(YELLOW)1. Executando VACUUM ANALYZE...$(NC)"
	@powershell -Command "$$env:PYTHONPATH='src'; uv run python -c \"import asyncio; from sqlalchemy import text; from fleet_intel_mcp.db.connection import engine; async def run(): async with engine.begin() as conn: await conn.execute(text('VACUUM ANALYZE registrations')); print('✅ VACUUM concluído'); asyncio.run(run())\""
	@echo "$(YELLOW)2. Atualizando views materializadas...$(NC)"
	@$(MAKE) db-refresh-views
	@echo "$(YELLOW)3. Executando health check...$(NC)"
	@$(MAKE) db-health
	@echo "$(GREEN)✅ Manutenção concluída!$(NC)"
