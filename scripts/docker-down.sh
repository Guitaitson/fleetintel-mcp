#!/bin/bash
# ==============================================================================
# FLEETINTEL MCP - STOP LOCAL ENVIRONMENT
# ==============================================================================
#
# Para todos os serviços Docker do ambiente local.
#
# Uso: ./scripts/docker-down.sh [--volumes]
#
# Opções:
#   --volumes    Remove também os volumes (CUIDADO: apaga dados)
#
# ==============================================================================

set -e

echo "🛑 Parando FleetIntel MCP - Ambiente Local"
echo ""

# Verificar flag --volumes
REMOVE_VOLUMES=false
if [ "$1" == "--volumes" ]; then
    REMOVE_VOLUMES=true
    echo "⚠️  Modo: REMOVER VOLUMES (dados serão apagados)"
    read -p "Tem certeza? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Operação cancelada."
        exit 1
    fi
fi

# Parar serviços
echo "📦 Parando serviços Docker..."
if [ "$REMOVE_VOLUMES" = true ]; then
    docker-compose -f docker-compose.local.yml down -v
    echo "✅ Serviços parados e volumes removidos."
else
    docker-compose -f docker-compose.local.yml down
    echo "✅ Serviços parados (volumes preservados)."
fi

echo ""
