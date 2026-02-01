#!/bin/bash
# ==============================================================================
# FLEETINTEL MCP - VIEW DOCKER LOGS
# ==============================================================================
#
# Exibe logs dos serviços Docker.
#
# Uso: ./scripts/docker-logs.sh [service_name]
#
# Exemplos:
#   ./scripts/docker-logs.sh           # Todos os serviços
#   ./scripts/docker-logs.sh redis     # Apenas Redis
#
# ==============================================================================

SERVICE=${1:-}

echo "📋 Logs do FleetIntel MCP"
echo ""

if [ -z "$SERVICE" ]; then
    docker-compose -f docker-compose.local.yml logs -f --tail=100
else
    docker-compose -f docker-compose.local.yml logs -f --tail=100 "$SERVICE"
fi
