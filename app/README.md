# FastAPI MCP Server - FleetIntel

FastAPI MCP Server implementation for Fleet Intelligence.

## 📋 Visão Geral

Este servidor implementa o protocolo MCP (Model Context Protocol) para fornecer acesso aos dados de frota do FleetIntel através de uma API REST.

## 🚀 Funcionalidades

### Endpoints Implementados

#### Health & Stats
- `GET /health` - Health check do servidor
- `GET /stats` - Estatísticas do banco de dados

#### Consultas de Veículos
- `POST /vehicles/query` - Busca de veículos por múltiplos critérios
  - Chassi (VIN)
  - Placa
  - Marca
  - Modelo
  - Ano de fabricação
  - Ano do modelo

#### Consultas de Empresas
- `POST /empresas/query` - Busca de empresas por múltiplos critérios
  - CNPJ
  - Razão social
  - Nome fantasia
  - Segmento de cliente
  - Grupo locadora

#### Consultas de Registros
- `POST /registrations/query` - Busca de registros de emplacamento
  - Data de emplacamento (início/fim)
  - Município
  - UF
  - Preço (mínimo/máximo)
  - Preço validado
  - Veículo (chassi/placa)

## 🏗 Arquitetura

```
app/
├── main.py              # Entry point do servidor
├── config.py             # Configurações (pydantic)
└── schemas/
    └── query_schemas.py  # Schemas Pydantic para queries/responses

src/
├── config/
│   └── settings.py      # Configurações de banco de dados
└── fleet_intel_mcp/
    ├── config.py           # Configurações do MCP
    └── db/
        └── connection.py   # Conexão com banco de dados
```

## 🔧 Configuração

### Variáveis de Ambiente

As configurações são gerenciadas através de `pydantic_settings`:

```python
# .env
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# Server
HOST=0.0.0.0
PORT=8000
APP_NAME=FleetIntel MCP Server
APP_VERSION=0.1.0
APP_DESCRIPTION=MCP Server for Fleet Intelligence

# Database
POOL_SIZE=20
MAX_OVERFLOW=30
POOL_RECYCLE=3600
STATEMENT_TIMEOUT=600000  # 10 minutos em milissegundos
```

### Configurações do Banco de Dados

- **Pool Size**: 20 conexões
- **Max Overflow**: 30 conexões adicionais
- **Pool Recycle**: 3600 segundos (1 hora)
- **Statement Timeout**: 600000ms (10 minutos)

## 📊 Schemas de Dados

### VehicleQuery
```python
class VehicleQuery(BaseModel):
    chassi: Optional[str]      # Chassi (VIN)
    placa: Optional[str]       # Placa
    marca: Optional[str]       # Marca
    modelo: Optional[str]      # Modelo
    ano_fabricacao_min: Optional[int]  # Ano de fabricação mínimo
    ano_fabricacao_max: Optional[int]  # Ano de fabricação máximo
    ano_modelo_min: Optional[int]  # Ano do modelo mínimo
    ano_modelo_max: Optional[int]  # Ano do modelo máximo
    limit: int = 100        # Limite de resultados (padrão: 100, máximo: 1000)
```

### Vehicle
```python
class Vehicle(BaseModel):
    id: int
    chassi: str
    placa: str
    marca: str
    modelo: str
    ano_fabricacao: int
    ano_modelo: int
```

### EmpresaQuery
```python
class EmpresaQuery(BaseModel):
    cnpj: Optional[str]           # CNPJ (exato)
    razao_social: Optional[str]  # Razão social (ILIKE)
    nome_fantasia: Optional[str]  # Nome fantasia (ILIKE)
    segmento_cliente: Optional[str]  # Segmento de cliente
    grupo_locadora: Optional[str]  # Grupo locadora
    limit: int = 100        # Limite de resultados
```

### Empresa
```python
class Empresa(BaseModel):
    id: int
    cnpj: str
    razao_social: Optional[str]
    nome_fantasia: Optional[str]
    segmento_cliente: Optional[str]
    grupo_locadora: Optional[str]
```

### RegistrationQuery
```python
class RegistrationQuery(BaseModel):
    data_emplacamento_inicio: Optional[str]  # Data de início (ISO)
    data_emplacamento_fim: Optional[str]     # Data de fim (ISO)
    municipio_emplacamento: Optional[str]  # Município (ILIKE)
    uf_emplacamento: Optional[str]           # UF (exato)
    preco_min: Optional[float]              # Preço mínimo
    preco_max: Optional[float]              # Preço máximo
    preco_validado: Optional[bool]         # Preço validado
    chassi: Optional[str]               # Chassi do veículo
    placa: Optional[str]                # Placa do veículo
    marca: Optional[str]                # Marca do veículo
    modelo: Optional[str]               # Modelo do veículo
    limit: int = 100        # Limite de resultados
```

### Registration
```python
class Registration(BaseModel):
    id: int
    data_emplacamento: str
    municipio_emplacamento: str
    uf_emplacamento: str
    preco: float
    preco_validado: Optional[bool]
    chassi: str
    placa: str
    marca: str
    modelo: str
    ano_fabricacao: int
    ano_modelo: int
    cnpj: str
    razao_social: Optional[str]
    nome_fantasia: Optional[str]
    segmento_cliente: Optional[str]
    grupo_locadora: Optional[str]
```

### StatsResponse
```python
class StatsResponse(BaseModel):
    marcas: int
    modelos: int
    vehicles: int
    empresas: int
    enderecos: int
    contatos: int
    registrations: int
```

## 🔒 Segurança

### Autenticação
- **CORS**: Habilitado para permitir requisições de qualquer origem
- **Rate Limiting**: Limite de 100 resultados por query
- **Input Validation**: Validação automática via Pydantic

### Proteção de Dados
- **SQL Injection**: Uso de queries parametrizadas (prevenção)
- **Row Level Security**: Implementado no banco de dados Supabase
- **Exposição de Dados**: Não expor dados sensíveis (CNPJ, CPF, etc.)

## 🚀 Como Executar

### Instalação de Dependências
```bash
# Criar ambiente virtual
uv venv

# Ativar ambiente
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instalar dependências
uv pip install fastapi uvicorn sqlalchemy asyncpg pydantic

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais do Supabase
```

### Executar o Servidor
```bash
# Modo de desenvolvimento
uv run uvicorn app.main:app --reload

# Modo de produção
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testar o Servidor
```bash
# Health check
curl http://localhost:8000/health

# Stats
curl http://localhost:8000/stats

# Query de veículos
curl -X POST http://localhost:8000/vehicles/query \
  -H "Content-Type: application/json" \
  -d '{"chassi": "9BWZZZZZ"}'

# Query de empresas
curl -X POST http://localhost:8000/empresas/query \
  -H "Content-Type: application/json" \
  -d '{"cnpj": "12345678000123"}'
```

## 📝 Documentação da API

### OpenAPI
A documentação automática do FastAPI está disponível em:
- `http://localhost:8000/docs` - Swagger UI
- `http://localhost:8000/redoc` - ReDoc

### Endpoints

#### Health Check
```
GET /health
Response: {
  "status": "healthy",
  "service": "fleetintel-mcp-server",
  "version": "0.1.0"
}
```

#### Stats
```
GET /stats
Response: {
  "marcas": 10,
  "modelos": 250,
  "vehicles": 10000,
  "empresas": 5739,
  "enderecos": 5739,
  "contatos": 5666,
  "registrations": 9443
}
```

#### Query de Veículos
```
POST /vehicles/query
Request: {
  "chassi": "9BWZZZZZ",
  "placa": "ABC1234",
  "marca": "VOLVO",
  "modelo": "FH",
  "ano_fabricacao_min": 2020,
  "ano_fabricacao_max": 2025,
  "limit": 100
}

Response: {
  "vehicles": [...],
  "count": 42
}
```

#### Query de Empresas
```
POST /empresas/query
Request: {
  "cnpj": "12345678000123",
  "razao_social": "FLEETINTEL",
  "segmento_cliente": "Locação",
  "limit": 100
}

Response: {
  "empresas": [...],
  "count": 15
}
```

#### Query de Registros
```
POST /registrations/query
Request: {
  "data_emplacamento_inicio": "2024-01-01",
  "data_emplacamento_fim": "2024-12-31",
  "municipio_emplacamento": "São Paulo",
  "uf_emplacamento": "SP",
  "preco_min": 50000.00,
  "preco_max": 150000.00,
  "chassi": "9BWZZZZZ",
  "limit": 100
}

Response: {
  "registrations": [...],
  "count": 87
}
```

## 🔄 Roadmap

### Versão 0.1.0 (Atual)
- ✅ Health check endpoint
- ✅ Stats endpoint
- ✅ Vehicle query endpoint
- ✅ Empresa query endpoint
- ✅ Registration query endpoint
- ✅ CORS middleware
- ✅ Pydantic schemas
- ✅ Database connection pooling
- ✅ Error handling

### Versão 0.2.0 (Planejada)
- [ ] Filtros avançados (data range, price range)
- [ ] Ordenação de resultados
- [ ] Paginação
- [ ] Cache de consultas frequentes
- [ ] Rate limiting avançado
- [ ] Autenticação e autorização
- [ ] Webhooks para notificações
- [ ] Batch operations para múltiplas queries
- [ ] Background jobs para consultas assíncronas

### Versão 1.0.0 (Futura)
- [ ] Integração com LangGraph
- [ ] Sistema de recomendações
- [ ] Análise preditiva de preços
- [ ] Alertas e notificações
- [ ] Export de dados em múltiplos formatos
- [ ] Dashboard administrativo

## 📝 Notas Importantes

### Performance
- Todos os endpoints usam `async/await` para operações de banco de dados
- Connection pooling configurado para 50 conexões
- Queries são parametrizadas para prevenir SQL injection
- Limite de 100 resultados por query para evitar sobrecarga

### Segurança
- Nunca expor credenciais do banco de dados
- Usar variáveis de ambiente para configurações sensíveis
- Implementar rate limiting em produção
- Validar todos os inputs antes de processar

### Compatibilidade
- Python 3.11+
- PostgreSQL 17.6+
- FastAPI 0.104+
- SQLAlchemy 2.0+
- Pydantic 2.5+

---

**Servidor FastAPI MCP Server implementado com sucesso!**

O servidor está pronto para uso e fornece acesso aos dados de frota do FleetIntel através de uma API REST moderna e eficiente.
