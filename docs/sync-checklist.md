# Checklist de Validação de Sincronização

## Pré-requisitos
- [ ] Tabela `sync_logs` criada no Supabase
- [ ] Variáveis ADMIN_API_KEY configuradas no ambiente
- [ ] Credenciais da API HubQuest válidas

## Testes Manuais
- [ ] Primeiro sync manual executado com sucesso:
  ```bash
  curl -X POST http://localhost:8000/admin/sync/trigger \
    -H "api-key: $ADMIN_API_KEY"
  ```
- [ ] Scheduler rodando no Docker:
  ```bash
  docker-compose logs mcp-server | grep "Scheduler iniciado"
  ```
- [ ] Logs estruturados validados:
  ```bash
  docker-compose logs mcp-server | grep "Métricas"
  ```

## Testes de Falha
- [ ] Retry testado com falha simulada (desligar API externa)
- [ ] Timeout de warm-up validado (configurar SYNC_TIMEOUT_WARMUP=5)

## Monitoramento
- [ ] Dashboard Grafana configurado com:
  - Duração média de sync
  - Taxa de registros por segundo
  - Taxa de falhas

## Documentação
- [ ] README.md atualizado com instruções
- [ ] Exemplos de consulta SQL adicionados
