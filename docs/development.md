# Guia de Desenvolvimento

## Epic 1: Bootstrap - Checklist

- [x] GT-12: Estrutura de diretórios criada
- [ ] GT-13: Dependencies (pyproject.toml + requirements.txt + lock)
- [ ] GT-14: Environment variables (.env.example)
- [ ] GT-15: Docker Compose local (Redis)
- [ ] GT-16: Makefile (comandos dev)

## Próximos Passos (após GT-12)

### GT-13: Configurar Dependências
Criar pyproject.toml com:
- FastAPI + Uvicorn
- LangGraph + LangChain
- Supabase client (postgrest-py)
- Redis client (redis-py)
- httpx (async HTTP)
- schedule (jobs)
- Linters: ruff, black
- Tests: pytest, pytest-asyncio

### GT-14: Variables de Ambiente
Documentar no .env.example:
- HUBQUEST_API_KEY
- SUPABASE_URL + SUPABASE_KEY
- REDIS_HOST + REDIS_PORT
- OPENAI_API_KEY
- LANGFUSE_* (opcional)
- EVOLUTION_API_TOKEN (futuro)

### GT-15: Docker Compose
Serviço Redis local:
- Imagem: redis:7-alpine
- Port: 6379
- Volume: redis_data
- Health check

### GT-16: Makefile
Comandos essenciais para DX (Developer Experience).
