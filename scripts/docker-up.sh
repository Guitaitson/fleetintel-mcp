#!/bin/bash
# ==============================================================================
# FLEETINTEL MCP - START LOCAL ENVIRONMENT
# ==============================================================================
#
# Inicia todos os serviços Docker para desenvolvimento local.
#
# Uso: ./scripts/docker-up.sh
#
# ==============================================================================

set -e

echo "🚀 Iniciando FleetIntel MCP - Ambiente Local"
echo ""

# Verificar se docker-compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose não encontrado. Instale antes de continuar."
    exit 1
fi

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "⚠️  Arquivo .env não encontrado."
    echo "   Copie .env.example para .env e configure:"
    echo "   cp .env.example .env"
    exit 1
fi

# Subir serviços
echo "📦 Iniciando serviços Docker..."
docker-compose -f docker-compose.local.yml up -d

# Aguardar health checks
echo ""
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 5

# Verificar status
echo ""
echo "📊 Status dos serviços:"
docker-compose -f docker-compose.local.yml ps

echo ""
echo "✅ Ambiente local iniciado com sucesso!"
echo ""
echo "🔗 Serviços disponíveis:"
echo "   Redis: localhost:6379"
echo "   Redis Commander: http://localhost:8081"
echo ""
echo "📝 Comandos úteis:"
echo "   Ver logs: ./scripts/docker-logs.sh"
echo "   Parar: ./scripts/docker-down.sh"
echo ""
