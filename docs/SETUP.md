# 📋 Setup Checklist - FleetIntel MCP

## Pré-requisitos

- [ ] Python 3.11+ instalado
- [ ] uv instalado (curl -LsSf https://astral.sh/uv/install.sh | sh)
- [ ] Git configurado
- [ ] Docker e Docker Compose (para desenvolvimento local)

## Configuração Inicial

- [ ] Clonar repositório
- [ ] Instalar dependências: `uv sync`
- [ ] Copiar .env.example para .env
- [ ] Configurar variáveis obrigatórias no .env
- [ ] Validar configuração: `python scripts/validate_env.py`
- [ ] Iniciar serviços locais: `docker-compose up -d` (próxima task)

## Configuração Docker Local

- [ ] Docker instalado e rodando
- [ ] Docker Compose instalado
- [ ] Iniciar ambiente: `./scripts/docker-up.sh`
- [ ] Verificar Redis: `docker exec -it fleetintel-redis redis-cli ping`
- [ ] Acessar Redis Commander: http://localhost:8081
- [ ] Todos os containers healthy: `docker-compose -f docker-compose.local.yml ps`

## Verificações

- [ ] Script de validação passa: ✅
- [ ] Conecta com Supabase: [testar depois]
- [ ] Conecta com Redis: [testar depois]
- [ ] Conecta com OpenAI: [testar depois]

## Problemas Comuns

[Será preenchido conforme surgem issues]
