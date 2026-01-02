# Variáveis de Ambiente - FleetIntel MCP

## Obrigatórias (aplicação não inicia sem elas)

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `FLEET_API_BASE_URL` | URL base da API externa | `https://api.com/v1` |
| `FLEET_API_KEY` | Chave de autenticação | `abc123...` |
| `SUPABASE_URL` | URL do projeto Supabase | `https://xxx.supabase.co` |
| `SUPABASE_ANON_KEY` | Supabase public key | `eyJhbG...` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service key | `eyJhbG...` |
| `API_SECRET_KEY` | Secret key da aplicação | Gerar com `openssl rand -hex 32` |

## Opcionais (têm valores padrão)

| Variável | Default | Descrição |
|----------|---------|-----------|
| `ENVIRONMENT` | `local` | Ambiente de execução |
| `DEBUG` | `false` | Modo debug |
| `LOG_LEVEL` | `INFO` | Nível de log |
| `REDIS_HOST` | `localhost` | Host do Redis |
| `REDIS_PORT` | `6379` | Porta do Redis |
| `REDIS_PASSWORD` | _vazio_ | Senha do Redis (obrigatória em prod) |
| `SERVER_PORT` | `8000` | Porta do servidor |
| `MAX_RECORDS_PER_QUERY` | `100` | Limite de registros |

## Como gerar valores seguros

### API_SECRET_KEY
```bash
openssl rand -hex 32
```

### REDIS_PASSWORD (produção)
```bash
openssl rand -base64 32
```

## Execução do Script de Validação

### Linux/macOS
```bash
# Tornar executável
chmod +x scripts/validate_env.py

# Executar
./scripts/validate_env.py
```

### Windows
```bash
# Executar via Python
python scripts/validate_env.py
```

## Ambientes

### Local (Desenvolvimento)
- DEBUG=true
- REDIS_HOST=localhost
- Sem REDIS_PASSWORD

### Staging (Homologação)
- DEBUG=false
- REDIS_HOST=<IP_VPS>
- COM REDIS_PASSWORD

### Production (Produção)
- DEBUG=false
- Use Infisical para todas as secrets
- Todos os valores obrigatórios preenchidos
