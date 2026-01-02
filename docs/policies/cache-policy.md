# Política de Cache - FleetIntel MCP

## Estratégia de Cache por Tipo de Dado
| Tipo de Dado | TTL | Estratégia |
|--------------|-----|------------|
| Cadastro de veículos | 24h | Cache agressivo |
| Status operacional | 5min | Cache moderado |
| Localização GPS | 1min | Cache mínimo |
| Histórico de viagens | 1h | Cache médio |
| Relatórios agregados | 6h | Cache agressivo |

## Implementação
- **Redis**: Armazenamento primário
- **Chave de cache**: `{user_id}:{filtros}:{timestamp}`
- **Invalidação manual**: Disponível para administradores
- **Cache compartilhado**: Quando os dados não são específicos de usuário

## Políticas de Refresco
- **Refresh automático**: 6h, 12h, 18h (horários de pico)
- **Forçar refresh**: Usuário pode solicitar (limite: 5/hora)
- **Warm-up**: Pré-carregar queries comuns às 5h

## Monitoramento
- **Métricas-chave**:
  - Taxa de hit/miss
  - Tempo economizado por consulta
  - Chamadas à API evitadas
- **Alertas**:
  - Taxa de hit < 70%
  - TTL expirado em > 5% das chaves

## Configurações (via .env)
```ini
CACHE_TTL_VEHICLE=86400    # 24h
CACHE_TTL_STATUS=300       # 5min
CACHE_TTL_LOCATION=60      # 1min
CACHE_TTL_TRIPS=3600       # 1h
CACHE_TTL_REPORTS=21600    # 6h
```
