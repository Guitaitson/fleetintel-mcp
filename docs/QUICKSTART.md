# FleetIntel MCP — Quickstart

> Setup completo do zero em menos de 15 minutos.

---

## Pré-requisitos

Antes de começar, garanta que você tem:

| Requisito | Verificar |
|-----------|-----------|
| Python 3.11 ou 3.12 | `python --version` |
| Docker Desktop (rodando) | `docker info` |
| [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes) | `uv --version` |
| [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) | `cloudflared --version` |
| Chave de API de dados de emplacamentos | variável `HUBQUEST_API_KEY` |

---

## Passo 1 — Clonar e instalar dependências

```bash
git clone https://github.com/SEU_USUARIO/fleetintel-mcp.git
cd fleetintel-mcp

# Criar ambiente virtual e instalar dependências
uv venv
.venv\Scripts\Activate.ps1         # Windows PowerShell
# source .venv/bin/activate         # Linux / macOS

uv pip install -e "."
```

---

## Passo 2 — Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais reais:

```env
# Banco de dados PostgreSQL (Docker local)
DATABASE_URL=postgresql+asyncpg://fleetintel:SUA_SENHA@127.0.0.1:5432/fleetintel

# Redis (Docker local)
REDIS_URL=redis://localhost:6379/1

# Token de autenticação do MCP Server (gere um token aleatório seguro)
MCP_AUTH_TOKEN=seu-token-secreto-aqui

# Senha do PostgreSQL no Docker Compose (deve bater com DATABASE_URL)
FLEETINTEL_DB_PASSWORD=SUA_SENHA

# Chave de acesso à API externa de dados de emplacamentos
HUBQUEST_API_KEY=sua-chave-da-api
```

> **Gerar um token seguro:**
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(32))"
> ```

---

## Passo 3 — Subir banco de dados e Redis

```bash
docker compose -f docker-compose.local.yml up -d
```

Aguarde ~10 segundos e verifique:

```bash
docker compose -f docker-compose.local.yml ps
```

Você deve ver `postgres` e `redis` com status `healthy`.

---

## Passo 4 — Carregar dados (carga inicial)

> Pule este passo se o banco já estiver populado.

```bash
# Sync completo (até 90 dias de histórico)
python scripts/sync_from_api.py --mode full --date-range 90

# Verificar saúde do banco
python scripts/db_health.py
```

A carga inicial pode demorar 30-60 minutos dependendo do volume. Acompanhe o progresso no terminal.

---

## Passo 5 — Iniciar o MCP Server

```bash
# Windows (use o Python do venv explicitamente)
.venv\Scripts\python.exe -m mcp_server.main

# Linux / macOS
python -m mcp_server.main
```

Você deve ver:

```
[FleetIntel MCP] Iniciando em modo streamable-http na porta 8888
INFO:     Uvicorn running on http://0.0.0.0:8888 (Press CTRL+C to quit)
```

**Teste local:**
```bash
curl -s http://localhost:8888/
# Deve retornar 404 (correto — o endpoint é /mcp)
```

---

## Passo 6 — Expor via Cloudflare Tunnel

### Opção A: Tunnel temporário (sem conta — URL muda a cada restart)

```bash
cloudflared tunnel --url http://localhost:8888
```

Copie a URL gerada (ex: `https://abc123.trycloudflare.com`).

### Opção B: Tunnel persistente (com conta Cloudflare — URL fixa)

```bash
# Autenticar
cloudflared tunnel login

# Criar tunnel (uma vez só)
cloudflared tunnel create fleetintel

# Configurar DNS (substitua pelo seu domínio)
cloudflared tunnel route dns fleetintel mcp.seu-dominio.com

# Iniciar com config
cloudflared tunnel --config infra/cloudflare-tunnel.yml run
```

> **Instalação como serviço Windows (inicia automaticamente):**
> ```powershell
> cloudflared service install --config "C:\caminho\para\infra\cloudflare-tunnel.yml"
> net start cloudflared
> ```

---

## Passo 7 — Conectar ao Claude Desktop

Abra o arquivo de configuração do Claude Desktop:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Adicione o servidor MCP:

```json
{
  "mcpServers": {
    "fleetintel": {
      "url": "https://mcp.seu-dominio.com/mcp",
      "headers": {
        "Authorization": "Bearer SEU_MCP_AUTH_TOKEN"
      }
    }
  }
}
```

Reinicie o Claude Desktop. Você deve ver as 7 tools do FleetIntel disponíveis.

---

## Verificação End-to-End

No Claude Desktop, envie:

> *"Use o FleetIntel para me dar estatísticas gerais do banco de dados."*

Se tudo estiver correto, o agente chamará `get_stats` e retornará algo como:

```
Total de veículos: 986.123
Total de empresas: 170.456
Total de emplacamentos: 1.023.891
Marcas cadastradas: 28
Modelos cadastrados: 834
```

---

## Troubleshooting

| Problema | Causa provável | Solução |
|---------|---------------|---------|
| `Connection refused` na porta 8888 | MCP Server não está rodando | Executar `python -m mcp_server.main` |
| `401 Unauthorized` | Token inválido | Verificar `MCP_AUTH_TOKEN` no `.env` e na config do Claude |
| `Database not healthy` | Docker não está rodando | `docker compose -f docker-compose.local.yml up -d` |
| Cloudflare tunnel offline | cloudflared parou | Reiniciar `cloudflared tunnel run` |
| Dados desatualizados | Sync não rodou | `python scripts/sync_from_api.py --mode incremental` |

---

## Próximos Passos

- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** — Roteiro guiado de uso com exemplos práticos
- **[DATA_SYNC.md](DATA_SYNC.md)** — Documentação completa da rotina de sync
- **[ARCHITECTURE.md](architecture.md)** — Arquitetura e referência técnica
