# Gestão de Usuários - FleetIntel MCP

## Modelo de Usuário MVP
- **Identificador primário**: Telefone WhatsApp (ex: +5511999999999)
- **Nome completo**: Registro obrigatório
- **Email corporativo**: Para contato oficial
- **Perfil**: 
  - Admin (acesso total)
  - Analyst (consulta avançada)
  - Viewer (consulta básica)
- **Status**: Ativo/Inativo
- **Data de criação**: Automática no registro
- **Aprovado por**: Admin responsável

## Processo de Onboarding
1. Usuário solicita acesso via WhatsApp
2. Admin recebe solicitação via painel
3. Admin aprova/rejeita com justificativa
4. Sistema envia credenciais via WhatsApp

## Lista Inicial de Usuários (exemplo YAML)
```yaml
users:
  - phone: "+5511999999999"
    name: "Admin Principal"
    email: "admin@empresa.com"
    role: "admin"
    status: "active"
    approved_by: "system"
    created_at: "2026-01-02"
```

## Políticas de Acesso
- Usuário não cadastrado: "Acesso negado. Solicite autorização."
- Usuário inativo: "Sua conta está desativada."
- Log de acesso: 
  - Todas as tentativas de autenticação
  - Consultas realizadas
  - Alterações de status
