# 🐳 Docker - Guia Técnico

## Visão Geral

Este projeto usa Docker para gerenciar dependências locais de desenvolvimento.
A configuração de produção será diferente e gerenciada via VPS.

## Arquitetura

```
┌─────────────────────────────────────────────┐
│          FleetIntel MCP (local)             │
├─────────────────────────────────────────────┤
│                                              │
│  ┌──────────────┐      ┌──────────────┐    │
│  │    Redis     │◄─────┤  Aplicação   │    │
│  │  (cache/queue)│      │   Python     │    │
│  └──────────────┘      └──────────────┘    │
│         │                       │            │
│         │                       │            │
│  ┌──────────────┐               │            │
│  │    Redis     │               │            │
│  │  Commander   │               ▼            │
│  │   (debug)    │        Supabase (cloud)   │
│  └──────────────┘                            │
│                                              │
└─────────────────────────────────────────────┘
```

## Serviços

### Redis

- **Imagem:** redis:7-alpine
- **Propósito:** Cache de consultas e gerenciamento de filas
- **Persistência:** Volume `redis-data` montado em `/data`
- **Configuração:**
    - maxmemory: 256mb (suficiente para dev)
    - maxmemory-policy: allkeys-lru
    - appendonly: yes (persistência AOF)
- **Health Check:** `redis-cli ping` a cada 30s

### Redis Commander (opcional)

- **Imagem:** rediscommander/redis-commander:latest
- **Propósito:** Interface web para debug e inspeção do Redis
- **Acesso:** http://localhost:8081
- **Uso:** Visualizar chaves, valores, estatísticas

## Rede

**Nome:** fleetintel-network
**Driver:** bridge
**Isolamento:** Serviços Docker se comunicam via nomes de container

## Volumes

### redis-data

- **Tipo:** Named volume
- **Localização:** Gerenciado pelo Docker
- **Backup:** Não necessário para dev (dados podem ser recriados)
- **Limpeza:** `docker-compose -f docker-compose.local.yml down -v`

## Configurações de Desenvolvimento vs Produção

| Aspecto | Desenvolvimento | Produção |
| :-- | :-- | :-- |
| Redis | Docker local | VPS ou Redis Cloud |
| Postgres | Supabase cloud | Supabase cloud |
| Persistência | Volume local | Backups automáticos |
| Monitoring | Redis Commander | Grafana + Prometheus |
| Logs | Docker logs | Centralizado (Loki) |

## Performance

### Limites de Recursos (futuro)

Atualmente sem limites para desenvolvimento. Para produção, adicionar:

```yaml
resources:
  limits:
    cpus: '0.5'
    memory: 512M
```

## Segurança

### Desenvolvimento

- Portas expostas localmente (sem autenticação forte)
- Dados não sensíveis
- Sem TLS

### Produção

- Redis com senha (requirepass)
- TLS para conexões
- Firewall limitando acessos
- Secrets via Doppler/Vault

## Troubleshooting Avançado

### Redis Lento

```bash
# Verificar stats
docker exec -it fleetintel-redis redis-cli INFO stats

# Verificar comandos lentos
docker exec -it fleetintel-redis redis-cli SLOWLOG GET 10
```

### Espaço em Disco

```bash
# Verificar uso de volumes
docker system df -v

# Limpar volumes não utilizados
docker volume prune
```

### Inspecionar Rede

```bash
# Ver detalhes da rede
docker network inspect fleetintel-network

# Testar conectividade entre containers
docker exec -it fleetintel-redis ping fleetintel-redis-ui
```

## Referências

- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Redis Docker Image](https://hub.docker.com/_/redis)
- [Redis Commander](https://github.com/joeferner/redis-commander)
