# FleetIntel MCP — Sincronização de Dados

> Documentação completa da rotina de atualização incremental do banco de dados.

---

## Visão Geral

O banco de dados do FleetIntel é alimentado por uma API externa de emplacamentos de veículos pesados. A sincronização é feita via script Python independente (`scripts/sync_from_api.py`), completamente desacoplado do servidor MCP.

**Princípio de design**: o sync é **idempotente** — pode ser executado múltiplas vezes sem duplicar dados. Usa `ON CONFLICT ... DO UPDATE` para garantir que registros existentes sejam atualizados corretamente.

---

## Modos de Operação

### Modo Incremental (uso diário recomendado)

```bash
python scripts/sync_from_api.py --mode incremental
```

- Busca registros dos **últimos 7 dias** por padrão (configurável com `--days`)
- Usa `date_type=atualizacao` para capturar registros que foram atualizados retroativamente
- Ideal para execução diária via agendador de tarefas
- Tempo estimado: 2-10 minutos

```bash
# Personalizar janela de tempo
python scripts/sync_from_api.py --mode incremental --days 14

# Dry-run: simula sem escrever no banco
python scripts/sync_from_api.py --mode incremental --dry-run
```

### Modo Full (carga inicial)

```bash
python scripts/sync_from_api.py --mode full --date-range 90
```

- Busca **todos os registros** no período especificado
- Usa `date_type=emplacamento` (data do emplacamento)
- Máximo de 90 dias por execução (limite da API)
- Para carga histórica completa, execute múltiplas vezes com períodos diferentes
- Tempo estimado: 30-60 minutos para 90 dias

---

## Parâmetros Disponíveis

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `--mode` | str | `incremental` | `incremental` ou `full` |
| `--days` | int | `7` | Janela em dias para modo incremental |
| `--date-range` | int | `90` | Período em dias para modo full |
| `--date-type` | str | auto | `emplacamento` ou `atualizacao` |
| `--dry-run` | flag | `False` | Simula sem gravar no banco |

---

## Lógica de Upsert

O script implementa upsert idempotente em todas as tabelas:

### Veículos
```sql
INSERT INTO vehicles (chassi, placa, marca_id, modelo_id, ...)
VALUES (...)
ON CONFLICT (chassi) DO UPDATE SET
    placa = EXCLUDED.placa,
    updated_at = NOW()
```

### Empresas
```sql
INSERT INTO empresas (cnpj, razao_social, nome_fantasia, ...)
VALUES (...)
ON CONFLICT (cnpj) DO UPDATE SET
    razao_social = EXCLUDED.razao_social,
    updated_at = NOW()
```

### Emplacamentos
```sql
INSERT INTO registrations (vehicle_id, data_emplacamento, empresa_id, ...)
VALUES (...)
ON CONFLICT (vehicle_id, data_emplacamento) DO UPDATE SET
    preco = EXCLUDED.preco,
    updated_at = NOW()
```

---

## Paginação da API

A API externa tem limite de **1000 registros por página**. O script itera automaticamente por todas as páginas:

```
Página 0: registros 0-999
Página 1: registros 1000-1999
Página 2: registros 2000-2999
...
Página N: último lote
```

O script detecta o fim da paginação quando:
- O número de resultados retornados é menor que o `limit` solicitado
- Ou quando `page >= pagination.pages_total`

---

## Warm-up da API

A API externa pode ter **cold-start** de alguns segundos após período de inatividade. O script implementa warm-up automático:

1. Faz uma requisição de aquecimento antes do sync principal
2. Aguarda até 60 segundos por uma resposta bem-sucedida
3. Só inicia o sync após confirmar que a API está responsiva

---

## Retry com Backoff Exponencial

Para erros de rede ou timeouts temporários:

| Tentativa | Aguarda antes de tentar |
|-----------|------------------------|
| 1ª (inicial) | — |
| 2ª retry | 5 segundos |
| 3ª retry | 10 segundos |
| 4ª retry | 20 segundos |
| Falha definitiva | Registra erro em sync_logs |

---

## Registro de Execuções (sync_logs)

Cada execução do sync é registrada na tabela `sync_logs`:

```sql
SELECT * FROM sync_logs ORDER BY started_at DESC LIMIT 5;
```

| Coluna | Descrição |
|--------|-----------|
| `mode` | `incremental` ou `full` |
| `date_type` | `emplacamento` ou `atualizacao` |
| `date_range` | Período consultado |
| `started_at` | Timestamp de início |
| `finished_at` | Timestamp de fim |
| `status` | `success`, `error`, ou `running` |
| `records_fetched` | Total de registros recebidos da API |
| `records_upserted` | Total de registros gravados no banco |
| `records_failed` | Total de erros de inserção |
| `pages_fetched` | Total de páginas consumidas |
| `error_message` | Mensagem de erro (se houver) |

---

## Agendamento Automático

### Windows — Task Agendada

```powershell
# Criar task agendada para sync diário às 03:00
$action = New-ScheduledTaskAction `
    -Execute "C:\caminho\para\fleetintel-mcp\.venv\Scripts\python.exe" `
    -Argument "scripts\sync_from_api.py --mode incremental" `
    -WorkingDirectory "C:\caminho\para\fleetintel-mcp"

$trigger = New-ScheduledTaskTrigger -Daily -At 3am

Register-ScheduledTask `
    -TaskName "FleetIntel-Sync" `
    -Action $action `
    -Trigger $trigger `
    -RunLevel Highest
```

### Linux / macOS — Cron

```bash
# Editar crontab
crontab -e

# Adicionar linha (sync diário às 03:00 UTC)
0 3 * * * cd /caminho/para/fleetintel-mcp && .venv/bin/python scripts/sync_from_api.py --mode incremental >> logs/sync_cron.log 2>&1
```

---

## Variáveis de Ambiente Necessárias

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `HUBQUEST_API_KEY` | Chave de acesso à API externa |
| `HUBQUEST_API_URL` | URL da API (padrão: configurado no script) |

---

## Verificação de Saúde do Banco

```bash
python scripts/db_health.py
```

Saída esperada:
```
=== FleetIntel DB Health Check ===
✓ Connection: OK
✓ vehicles: 986,123 registros
✓ empresas: 170,456 registros
✓ registrations: 1,023,891 registros
✓ sync_logs: último sync há 18h (status: success)
```

---

## Troubleshooting

| Problema | Causa | Solução |
|---------|-------|---------|
| `API key invalid` | Chave expirada ou incorreta | Verificar `HUBQUEST_API_KEY` no `.env` |
| `Connection timeout` durante warm-up | API em cold-start | Aguardar ou aumentar timeout no script |
| `ON CONFLICT` errors | Schema desatualizado | Executar `setup_db_schema()` no script |
| Sync parou no meio | Erro de rede ou timeout | Re-executar: o upsert é idempotente |
| Dados ausentes | API retornou menos que esperado | Verificar `sync_logs.records_fetched` vs `records_upserted` |
