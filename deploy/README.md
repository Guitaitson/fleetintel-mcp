# Deploy Configuration

Configurações Docker e scripts de deploy para Coolify.

## Arquivos

- `Dockerfile`: Imagem Python otimizada
- `docker-compose.prod.yml`: Stack produção (sem Redis local)
- `coolify.json`: Configuração Coolify deployment
- `healthcheck.sh`: Script health check para containers

## Deploy Strategy

- Build: Multi-stage Dockerfile (builder + runtime)
- Registry: Docker Hub (privado)
- Orchestration: Coolify no VPS
- Rollback: Tags de versão semântica
