# FleetIntel MCP Server

Model Context Protocol (MCP) Server para consulta de dados de frota veicular.

## Descrição

Este servidor implementa o protocolo MCP (Model Context Protocol) permitindo que agentes de IA como Claude Desktop consultem diretamente o banco de dados FleetIntel para obter informações sobre veículos, empresas e registros de emplacamento.

## Ferramentas Disponíveis

### 1. search_vehicles
Buscar veículos por chassi, placa, marca, modelo ou faixa de ano.

**Parâmetros:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| chassi | string | Chassi do veículo (exato) |
| placa | string | Placa do veículo (ILIKE) |
| marca | string | Nome da marca (ILIKE) |
| modelo | string | Nome do modelo (ILIKE) |
| ano_fabricacao_min | integer | Ano mínimo de fabricação |
| ano_fabricacao_max | integer | Ano máximo de fabricação |
| limit | integer | Máximo de resultados (padrão: 100, máx: 1000) |

**Exemplo de uso:**
```python
# Claude Desktop pode chamar:
await search_vehicles(marca="FIAT", limit=10)
```

### 2. search_empresas
Buscar empresas (locadoras, frotistas) por CNPJ, razão social, nome fantasia, segmento ou grupo.

**Parâmetros:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| cnpj | string | CNPJ (14 dígitos, exato) |
| razao_social | string | Razão social (ILIKE) |
| nome_fantasia | string | Nome fantasia (ILIKE) |
| segmento_cliente | string | Segmento do cliente (ILIKE) |
| grupo_locadora | string | Grupo da locadora (ILIKE) |
| limit | integer | Máximo de resultados (padrão: 100, máx: 1000) |

**Exemplo de uso:**
```python
await search_empresas(segmento_cliente="LOCADORA", limit=20)
```

### 3. search_registrations
Buscar registros de emplacamento por data, município, UF, faixa de preço ou detalhes do veículo/empresa.

**Parâmetros:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| data_emplacamento_inicio | string | Data início (YYYY-MM-DD) |
| data_emplacamento_fim | string | Data fim (YYYY-MM-DD) |
| municipio_emplacamento | string | Município (ILIKE) |
| uf_emplacamento | string | UF do emplacamento (ex: "SP") |
| preco_min | number | Preço mínimo |
| preco_max | number | Preço máximo |
| preco_validado | boolean | Flag de preço validado |
| chassi | string | Chassi do veículo (exato) |
| placa | string | Placa do veículo (ILIKE) |
| marca | string | Marca do veículo (ILIKE) |
| modelo | string | Modelo do veículo (ILIKE) |
| limit | integer | Máximo de resultados (padrão: 100, máx: 1000) |

**Exemplo de uso:**
```python
await search_registrations(
    uf_emplacamento="SP",
    data_emplacamento_inicio="2024-01-01",
    data_emplacamento_fim="2024-12-31",
    limit=50
)
```

### 4. get_stats
Obter estatísticas do banco de dados.

**Retorna:**
```json
{
  "marcas": 45,
  "modelos": 320,
  "vehicles": 986859,
  "empresas": 161932,
  "enderecos": 161932,
  "contatos": 155622,
  "registrations": 919941
}
```

## Configuração para Claude Desktop

### Opção 1: Usando Claude Desktop com MCP SDK

1. Instale o Claude Desktop (versão mais recente)

2. Configure o servidor MCP no arquivo `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fleetintel": {
      "command": "python",
      "args": ["-m", "mcp_server.main"],
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_SERVICE_KEY": "your-service-role-key"
      }
    }
  }
}
```

3. Reinicie o Claude Desktop

### Opção 2: Executar Manualmente

```bash
# Ativar ambiente virtual
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Instalar dependências
uv pip install -e .

# Executar servidor MCP
python -m mcp_server.main
```

## Exemplos de Queries

### Buscar veículos FIAT Placa starting with "ABC":
```
Claude: Busca os veículos FIAT com placa começando com ABC
MCP Tool: search_vehicles(marca="FIAT", placa="ABC", limit=20)
```

### Contar emplacamentos em São Paulo em 2024:
```
Claude: Quantos emplacamentos foram feitos em SP em 2024?
MCP Tool: search_registrations(
    uf_emplacamento="SP",
    data_emplacamento_inicio="2024-01-01",
    data_emplacamento_fim="2024-12-31",
    limit=1
)
```

### Listar top 10 empresas do segmento LOCADORA:
```
Claude: Lista as 10 maiores locadoras
MCP Tool: search_empresas(segmento_cliente="LOCADORA", limit=10)
```

### Verificar estatísticas do banco:
```
Claude: Mostre as estatísticas do banco de dados
MCP Tool: get_stats()
```

## Instalação

```bash
# Clone o repositório
git clone https://github.com/Guitaitson/fleetintel-mcp.git
cd fleetintel-mcp

# Crie o ambiente virtual
uv venv
.venv\Scripts\activate  # Windows

# Instale as dependências
uv pip install -e .

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas credenciais do Supabase
```

## Variáveis de Ambiente

| Variável | Descrição | Obrigatório |
|----------|-----------|-------------|
| SUPABASE_URL | URL do projeto Supabase | Sim |
| SUPABASE_SERVICE_KEY | Service Role Key do Supabase | Sim |
| DATABASE_URL | URL de conexão PostgreSQL | Opcional (usa Supabase) |

## Testes

```bash
# Executar testes das tools MCP
python -m mcp_server.test_mcp_tools
```

## Estrutura do Projeto

```
mcp_server/
├── main.py              # Servidor MCP principal
├── test_mcp_tools.py    # Script de testes
└── README.md           # Esta documentação
```

## Banco de Dados

O servidor conecta-se ao PostgreSQL do Supabase com as seguintes tabelas:

- **marcas**: Marcas de veículos (FIAT, VW, GM, etc.)
- **modelos**: Modelos de veículos (Uno, Gol, Onix, etc.)
- **vehicles**: Veículos cadastrados (986K registros)
- **empresas**: Empresas/Locadoras (161K registros)
- **enderecos**: Endereços das empresas
- **contatos**: Contatos das empresas
- **registrations**: Registros de emplacamento (919K registros)

## Licença

MIT
