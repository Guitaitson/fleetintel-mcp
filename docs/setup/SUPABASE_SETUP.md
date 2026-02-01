# 🚀 Guia de Configuração do Supabase

## 📋 Problema Identificado

O erro `getaddrinfo failed` ocorre porque o `DATABASE_URL` no arquivo `.env` está configurado para um hostname Docker (`db:5432`) que não existe quando executamos scripts localmente.

## ✅ Solução: Configurar Supabase Real

### Opção 1: Usar Supabase Cloud (RECOMENDADO)

#### 1. Criar Projeto no Supabase

```bash
# Acesse: https://supabase.com/dashboard
# Clique em "New Project"
# Preencha:
#   - Nome do projeto: fleetintel-mcp
#   - Database Password: (escolha uma senha forte)
#   - Region: South America (sao-paulo)
```

#### 2. Obter Credenciais

Após criar o projeto, vá para **Settings > API**:

```bash
# Project URL
https://seu-projeto-id.supabase.co

# anon/public key
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# service_role key (⚠️ MANTENHA SECRETO!)
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Vá para **Settings > Database**:

```bash
# Connection string (Direct connection)
postgresql://postgres.seu-projeto-id:[SUA-SENHA]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
```

#### 3. Atualizar .env

```bash
# Edite o arquivo .env:
SUPABASE_URL=https://seu-projeto-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres.seu-projeto-id:[SUA-SENHA]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
ADMIN_API_KEY=seu_segredo_personalizado_aqui
```

#### 4. Executar Migrações

```bash
make migrate
```

---

### Opção 2: Usar Supabase Local com Docker

#### 1. Subir Stack Local

```bash
make dev
```

#### 2. Atualizar .env para Localhost

```bash
# Edite o arquivo .env:
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
ADMIN_API_KEY=seu_segredo_aqui
```

> **Nota:** Você precisa mapear a porta 5432 no `docker-compose.local.yml`

#### 3. Executar Migrações

```bash
make migrate
```

---

## 🎯 Próximos Passos

Após configurar o Supabase:

1. ✅ Migrações serão aplicadas com sucesso
2. ✅ Você poderá desenvolver e testar localmente
3. ✅ Conexão funcionará tanto em dev quanto produção

## 🔍 Troubleshooting

### Erro: `getaddrinfo failed`
- **Causa:** DATABASE_URL aponta para hostname Docker inexistente
- **Solução:** Seguir este guia e usar credenciais reais

### Erro: `ModuleNotFoundError: No module named 'fleet_intel_mcp'`
- **Causa:** PYTHONPATH não está configurado
- **Solução:** O Makefile já resolve automaticamente

### Erro: `ValidationError for Settings`
- **Causa:** Campos extras no .env não mapeados em config.py
- **Solução:** Verifique se todos os campos em .env existem em `src/fleet_intel_mcp/config.py`

### Erro: `Could not find the table 'public.registrations' in the schema cache` (PGRST205)
- **Causa:** PostgREST não enxerga a tabela no cache de schema, mesmo que ela exista no PostgreSQL
- **Solução:**
  1. Habilitar RLS (Row Level Security) na tabela - já implementado na migração `20260103000007_enable_rls.sql`
  2. Recarregar schema do PostgREST manualmente no Dashboard do Supabase:
     - Acesse: Settings → API → Reload schema
  3. Ou execute via SQL:
     ```sql
     NOTIFY pgrst, 'reload schema';
     ```
  4. **Nota:** SQLAlchemy conecta diretamente ao PostgreSQL e funciona normalmente. O problema é específico da API REST do Supabase.

---

## 📚 Referências

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase CLI](https://supabase.com/docs/guides/cli)
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)
