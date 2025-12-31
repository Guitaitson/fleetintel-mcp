#!/bin/bash
# Script de rollback para versão anterior

set -e

echo "=== FleetIntel MCP - Rollback Script ==="
echo ""

# Listar últimas 10 tags
echo "Últimas releases disponíveis:"
git tag -l | tail -n 10

echo ""
read -p "Digite a versão para rollback (ex: v0.1.0): " VERSION

# Validar se tag existe
if ! git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo "❌ Erro: Tag $VERSION não existe"
    exit 1
fi

echo ""
echo "⚠️  ATENÇÃO: Você vai fazer rollback para $VERSION"
echo "Isso irá:"
echo "1. Criar backup da versão atual"
echo "2. Voltar o código para $VERSION"
echo "3. Requerer redeploy manual"
echo ""
read -p "Continuar? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Rollback cancelado"
    exit 0
fi

# Criar branch de backup
BACKUP_BRANCH="backup/pre-rollback-$(date +%Y%m%d-%H%M%S)"
git checkout -b "$BACKUP_BRANCH"
git push origin "$BACKUP_BRANCH"
echo "✅ Backup criado em: $BACKUP_BRANCH"

# Fazer rollback
git checkout main
git reset --hard "$VERSION"
echo "✅ Código revertido para $VERSION"
echo ""
echo "⚠️  PRÓXIMOS PASSOS:"
echo "1. Revisar mudanças: git diff origin/main"
echo "2. Force push (use com cuidado): git push --force origin main"
echo "3. Redeploy no servidor"
echo "4. Testar aplicação"
