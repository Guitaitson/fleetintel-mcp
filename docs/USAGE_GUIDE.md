# FleetIntel MCP — Guia de Uso

> Roteiro guiado: desde a conexão do servidor ao seu agente até a extração de insights valiosos sobre a frota de veículos pesados do Brasil.

---

## Parte 1 — Conectando o FleetIntel ao seu Agente

### Claude Desktop

1. Abra (ou crie) o arquivo de configuração:
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Adicione o bloco `mcpServers`:

```json
{
  "mcpServers": {
    "fleetintel": {
      "url": "https://mcp.gtaitson.space/mcp",
      "headers": {
        "Authorization": "Bearer SEU_MCP_AUTH_TOKEN"
      }
    }
  }
}
```

3. Salve e **reinicie o Claude Desktop**.

4. Verifique: no canto inferior esquerdo do Claude Desktop, você deve ver um ícone de ferramentas. Clique para confirmar que as 7 tools do FleetIntel estão listadas.

---

### AgentVPS (ou qualquer agente com suporte a MCP HTTP)

Configure o servidor MCP nas definições do seu agente:

```
URL:     https://mcp.gtaitson.space/mcp
Auth:    Bearer SEU_MCP_AUTH_TOKEN
Headers: Authorization: Bearer SEU_MCP_AUTH_TOKEN
         Content-Type: application/json
         Accept: application/json, text/event-stream
```

Para agentes que usam a SDK do MCP diretamente:

```python
from mcp.client.streamable_http import streamablehttp_client

async with streamablehttp_client(
    url="https://mcp.gtaitson.space/mcp",
    headers={"Authorization": "Bearer SEU_TOKEN"}
) as (read, write, _):
    # seu agente aqui
```

---

## Parte 2 — Primeiros Passos: Validando a Conexão

Assim que o agente estiver conectado, comece com perguntas simples para validar que tudo funciona:

---

### ✅ Teste 1: Estatísticas gerais

> *"Quantos veículos, empresas e emplacamentos existem na base de dados do FleetIntel?"*

O agente chama `get_stats` e retorna algo como:
```
Base de dados FleetIntel:
- 986.123 veículos cadastrados
- 170.456 empresas proprietárias
- 1.023.891 emplacamentos registrados
- 28 marcas, 834 modelos
```

---

### ✅ Teste 2: Busca simples de veículo

> *"Busca veículos da marca SCANIA com ano de fabricação entre 2022 e 2024."*

O agente chama `search_vehicles` com `marca="SCANIA"`, `ano_min=2022`, `ano_max=2024`.

---

## Parte 3 — Análise de Mercado

### Market Share por Marca

> *"Qual o market share das marcas de caminhão no Brasil em 2024?"*

O agente chama `get_market_share(year=2024)` e retorna:

```
Market Share — Caminhões Brasil 2024:
1. MARCA_A:  18,2% (12.340 unidades)
2. MARCA_B:  16,5% (11.200 unidades)
3. MARCA_C:  14,1% (9.580 unidades)
...
```

---

### Market Share por Estado

> *"Qual o market share de caminhões no Rio Grande do Sul em 2024?"*

```
get_market_share(year=2024, uf="RS")
```

---

### Evolução Anual

> *"Compare o market share de marcas de caminhão entre 2022 e 2024."*

O agente faz 3 chamadas a `get_market_share` (uma por ano) e consolida os resultados.

---

## Parte 4 — Análise de Empresas

### Top Compradores do Ano

> *"Quais as 10 empresas que mais compraram veículos pesados no Brasil em 2024?"*

```
top_empresas_by_registrations(year=2024, limit=10)
```

Retorno:
```
Top 10 compradores de veículos pesados — Brasil 2024:
1. EMPRESA ALFA TRANSPORTES LTDA        - 342 unidades
2. BETA LOGÍSTICA E DISTRIBUIÇÃO S.A.   - 298 unidades
3. GAMA FROTAS RODOVIÁRIAS              - 276 unidades
...
```

---

### Top Compradores por Estado

> *"Quais empresas mais compraram caminhões em São Paulo em 2025?"*

```
top_empresas_by_registrations(year=2025, uf="SP", limit=10)
```

---

### Histórico de Compras de uma Empresa

> *"Quantos veículos a empresa 'TRANSPORTES ALFA' emplacou nos últimos 3 anos?"*

O agente faz 3 chamadas a `count_empresa_registrations`:

```
count_empresa_registrations(empresa_nome="TRANSPORTES ALFA", year=2022) → 87
count_empresa_registrations(empresa_nome="TRANSPORTES ALFA", year=2023) → 124
count_empresa_registrations(empresa_nome="TRANSPORTES ALFA", year=2024) → 156
```

Resultado: crescimento de 79% em 3 anos.

---

### Pesquisa de Empresa por Nome

> *"Encontre informações sobre a empresa 'RODOVIÁRIO PAULISTA'."*

```
search_empresas(razao_social="RODOVIÁRIO PAULISTA")
```

Retorna: CNPJ, razão social, nome fantasia, endereço, segmento, contatos.

---

## Parte 5 — Análise de Emplacamentos

### Emplacamentos por Período e Região

> *"Liste os emplacamentos de caminhões acima de R$ 500.000 no Paraná em janeiro de 2025."*

```
search_registrations(
    data_inicio="2025-01-01",
    data_fim="2025-01-31",
    uf="PR",
    preco_min=500000
)
```

---

### Volume por Mês

> *"Quantos veículos foram emplacados por mês em 2024 no Brasil?"*

O agente faz 12 chamadas a `search_registrations` com `data_inicio` e `data_fim` para cada mês.

---

### Emplacamentos de uma Empresa Específica

> *"Quais veículos a empresa de CNPJ 12.345.678/0001-90 emplacou em 2024?"*

```
search_registrations(empresa_cnpj="12345678000190")
```

---

## Parte 6 — Casos de Uso Avançados

### Identificar Clientes em Expansão de Frota

> *"Encontre empresas que mais cresceram em compras de veículos pesados entre 2023 e 2024 no Brasil."*

Fluxo do agente:
1. `top_empresas_by_registrations(year=2023, limit=50)` → lista A
2. `top_empresas_by_registrations(year=2024, limit=50)` → lista B
3. Cruza as listas e calcula variação percentual
4. Retorna empresas com maior crescimento

---

### Análise Competitiva Regional

> *"Em quais estados a MARCA_X tem maior market share? Compare com a MARCA_Y."*

Fluxo:
1. Para cada UF: `get_market_share(year=2024, uf=UF)`
2. Filtra resultados por marca
3. Monta mapa comparativo

---

### Prospecção de Clientes

> *"Liste empresas de transporte de carga em Minas Gerais que compraram mais de 20 caminhões em 2024."*

Fluxo:
1. `search_empresas(uf="MG", segmento="transporte")` → lista de empresas
2. Para cada empresa: `count_empresa_registrations(empresa_nome=nome, year=2024)`
3. Filtra as que têm ≥ 20 emplacamentos

---

### Ticket Médio por Segmento

> *"Qual o ticket médio de caminhões acima de 300cv emplacados em 2024?"*

```
search_registrations(
    data_inicio="2024-01-01",
    data_fim="2024-12-31",
    preco_min=100000,
    limit=200
)
```

O agente calcula a média dos valores `preco` retornados.

---

## Parte 7 — Boas Práticas para Agentes

### Seja específico nos filtros

❌ Evite perguntas muito amplas sem filtros de período:
> *"Liste todos os emplacamentos."*

✅ Prefira perguntas com escopo definido:
> *"Liste emplacamentos de caminhões acima de R$300k no RS em 2024."*

---

### Combine múltiplas tools

As tools se complementam. Um insight completo geralmente vem de 2-3 chamadas:

```
1. top_empresas_by_registrations → identifica quem mais compra
2. search_empresas → busca dados de contato dessas empresas
3. count_empresa_registrations → valida histórico de compras
```

---

### Use anos completos para análises de mercado

Para market share e rankings, sempre especifique o ano completo:

```
get_market_share(year=2024)           ✅ Ano completo
get_market_share(year=2024, uf="SP")  ✅ Ano + estado
```

---

### Resultados paginados

O `limit` máximo varia por tool:
- `search_vehicles`: máx 100
- `search_empresas`: máx 100
- `search_registrations`: máx 200
- `top_empresas_by_registrations`: máx 50

Para análises que precisam de mais resultados, faça múltiplas chamadas com filtros diferentes.

---

## Parte 8 — Referência Rápida das Tools

| Tool | O que faz | Parâmetros chave |
|------|-----------|-----------------|
| `get_stats` | Contagem geral do banco | — |
| `search_vehicles` | Busca veículos | chassi, marca, modelo, ano_min, ano_max |
| `search_empresas` | Busca empresas | cnpj, razao_social, uf, segmento |
| `search_registrations` | Busca emplacamentos | data_inicio, data_fim, uf, preco_min, preco_max |
| `top_empresas_by_registrations` | Ranking de compradores | year, uf, limit |
| `count_empresa_registrations` | Volume de uma empresa | empresa_nome, year |
| `get_market_share` | Share de mercado por marca | year, uf, segmento |

---

## Parte 9 — Prompt de Sistema Recomendado

Se você estiver configurando um agente especializado em frota, use este prompt de sistema como base:

```
Você é um analista especializado em frota de veículos pesados do Brasil.
Você tem acesso a uma base de dados com ~1 milhão de emplacamentos de
caminhões, ônibus e implementos, cobrindo ~986 mil veículos e ~170 mil
empresas proprietárias.

Ao responder perguntas:
1. Use as tools disponíveis para buscar dados reais — nunca invente números
2. Sempre especifique o período e a fonte dos dados na resposta
3. Para análises de mercado, prefira year completo (ex: 2024) a períodos parciais
4. Quando uma pergunta exigir múltiplas tools, execute-as em sequência e consolide
5. Apresente números com separadores de milhar (986.123, não 986123)
6. Indique limitações quando o dado solicitado não estiver disponível
```
