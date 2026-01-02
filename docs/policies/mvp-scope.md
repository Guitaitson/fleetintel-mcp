# Escopo MVP - FleetIntel MCP

## O Que Está Incluído
✅ **Funcionalidades Principais**:
- Consulta de status de veículos via WhatsApp
- Autenticação por número de telefone
- Cache básico com Redis
- Filtros obrigatórios (UF, período)
- Logs de auditoria básicos

✅ **Endpoints MCP**:
- `GET /veiculos`: Listagem com filtros
- `GET /veiculos/{id}`: Detalhes do veículo
- `GET /historico`: Histórico de localização

✅ **Usuários**:
- Lista restrita (5 usuários máx)
- Perfis: Admin, Analyst, Viewer

## O Que Não Está Incluído
🚫 **Funcionalidades Excluídas**:
- Interface web administrativa
- Múltiplos métodos de autenticação
- Exportação de relatórios (PDF/Excel)
- Integração com sistemas de manutenção
- Análise de dados avançadas
- Suporte a multi-tenancy

## Critérios de Sucesso
🎯 **Métricas**:
- 95% das consultas respondidas em <5s
- 100% das queries com filtros obrigatórios
- 0 incidentes de vazamento de dados
- 85%+ taxa de acerto no cache

## Roadmap Pós-MVP
➡️ **Versão 1.0**:
- Dashboard de monitoramento
- Controle de acesso granular
- Notificações proativas
- Anonimização de dados para LGPD
- API para integração com ERPs

## Riscos Mitigados
🛡️ **Proteções**:
- Rate limiting em todas as consultas
- Bloqueio automático por uso excessivo
- Logs detalhados de todas as operações
- Backup diário dos dados críticos
