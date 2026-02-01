# MCP Server

FastAPI server implementando protocolo MCP (Model Context Protocol) para expor dados de frota.

## Responsabilidades

- Endpoints de consulta (veículos, motoristas, sinistros, multas)
- Validação de parâmetros via Pydantic
- Rate limiting e cache Redis
- Health checks e observabilidade
- Autenticação via API keys (futuro)

## Estrutura Planejada

mcp_server/
├── api/ # Rotas FastAPI
├── models/ # Pydantic models
├── services/ # Lógica de negócio
└── main.py # Entry point

## Integrações

- Supabase: queries otimizadas com índices
- Redis: cache de consultas frequentes (TTL 5min)
- LangGraph agent: processamento complexo de queries
