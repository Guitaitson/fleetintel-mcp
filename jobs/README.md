# Scheduled Jobs

Jobs agendados para sincronização e manutenção de dados.

## Jobs Implementados

### Sincronização Incremental (GT-10)
- **Frequência**: Semanal (Domingo 22h BRT)
- **Método**: `date_type=atualizacao` (últimos 8 dias)
- **Retry**: 3 tentativas com backoff exponencial
- **Warm-up**: Timeout estendido na primeira request

## Scheduler

- Biblioteca: `schedule` (Python)
- Execução: Container Docker separado
- Logs: Supabase `sync_logs` table
- Monitoramento: Integração futura com Langfuse
