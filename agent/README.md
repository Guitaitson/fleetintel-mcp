# LangGraph Agent

Agent conversacional para processar consultas complexas sobre dados de frota.

## Responsabilidades

- Interpretação de perguntas em linguagem natural
- Orquestração de múltiplas consultas
- Agregação e sumarização de resultados
- Geração de insights via LLM

## Arquitetura

- LangGraph para workflow stateful
- OpenAI GPT-4 como LLM backend
- Memória de contexto no Redis
- Ferramentas MCP server como tools

## Casos de Uso

- "Quantos veículos tiveram sinistros nos últimos 30 dias?"
- "Liste motoristas com mais de 3 multas este ano"
- "Compare custos de manutenção entre filiais"
