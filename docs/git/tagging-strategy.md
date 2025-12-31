ESTRATÉGIA DE VERSIONAMENTO (Semantic Versioning 2.0.0):

Formato: vMAJOR.MINOR.PATCH

- MAJOR (v1.0.0): Breaking changes, mudanças de arquitetura
- MINOR (v0.1.0): Novas features compatíveis
- PATCH (v0.0.1): Bug fixes e ajustes

CRONOLOGIA DE RELEASES PLANEJADA:
- v0.1.0 - MVP FastAPI MCP Server (GT-11 a GT-15)
- v0.2.0 - Agente LangGraph (GT-16 a GT-20)
- v0.3.0 - Integração WhatsApp (GT-21 a GT-25)
- v1.0.0 - Produção completa

COMO CRIAR TAG:
# Após merge em main
git checkout main
git pull
git tag -a v0.1.0 -m "Release v0.1.0: MVP FastAPI MCP Server"
git push origin v0.1.0

COMO LISTAR TAGS:
git tag -l

COMO VER DETALHES:
git show v0.1.0
