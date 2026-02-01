-- ============================================
-- SCRIPT DE DIAGNÓSTICO POSTGREST
-- ============================================
-- Execute este script no Supabase SQL Editor para diagnosticar
-- problemas de exposição de tabelas via API REST

-- 1. VERIFICAR CONFIGURAÇÃO DO AUTHENTICATOR (CRÍTICO)
-- O role authenticator precisa ter pgrst.db_schemas configurado
SELECT 
    setrole::regrole AS role_name,
    setconfig AS configuration
FROM pg_db_role_setting
WHERE setrole::regrole = 'authenticator'::regrole;

-- Resultado esperado: pgrst.db_schemas deve incluir 'public'
-- Se vazio ou NULL, este é o problema!

-- ============================================

-- 2. VERIFICAR SE TABELA EXISTE E ESTÁ ACESSÍVEL
SELECT 
    schemaname,
    tablename,
    tableowner,
    hasindexes,
    hasrules,
    hastriggers
FROM pg_tables 
WHERE tablename IN ('registrations', '_migrations')
ORDER BY tablename;

-- Resultado esperado: Ambas as tabelas devem aparecer no schema 'public'

-- ============================================

-- 3. VERIFICAR PERMISSÕES DOS ROLES
SELECT 
    grantee,
    table_schema,
    table_name,
    privilege_type
FROM information_schema.role_table_grants 
WHERE table_name IN ('registrations', '_migrations')
ORDER BY table_name, grantee, privilege_type;

-- Resultado esperado: roles 'anon' e 'authenticated' devem ter SELECT

-- ============================================

-- 4. VERIFICAR RLS (ROW LEVEL SECURITY)
SELECT 
    schemaname,
    tablename,
    tableowner,
    rowsecurity AS rls_enabled
FROM pg_tables 
WHERE tablename = 'registrations';

-- Resultado esperado: rls_enabled = true

-- ============================================

-- 5. VERIFICAR POLICIES (POLÍTICAS RLS)
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd AS command,
    qual AS using_expression
FROM pg_policies
WHERE tablename = 'registrations';

-- Resultado esperado: Deve existir pelo menos uma policy para SELECT

-- ============================================

-- 6. LISTAR TODOS OS SCHEMAS DISPONÍVEIS
SELECT 
    schema_name,
    schema_owner
FROM information_schema.schemata
ORDER BY schema_name;

-- ============================================

-- 7. VERIFICAR ROLES DISPONÍVEIS
SELECT 
    rolname,
    rolsuper,
    rolinherit,
    rolcreaterole,
    rolcreatedb,
    rolcanlogin
FROM pg_roles
WHERE rolname IN ('postgres', 'authenticator', 'anon', 'authenticated', 'service_role')
ORDER BY rolname;

-- ============================================
-- INTERPRETAÇÃO DOS RESULTADOS:
-- 
-- PROBLEMA 1: authenticator sem pgrst.db_schemas configurado
--   SOLUÇÃO: ALTER ROLE authenticator SET pgrst.db_schemas = 'public, storage';
--
-- PROBLEMA 2: Roles anon/authenticated sem permissões
--   SOLUÇÃO: GRANT SELECT ON public.registrations TO anon, authenticated;
--
-- PROBLEMA 3: RLS ativo mas sem policies
--   SOLUÇÃO: CREATE POLICY para permitir SELECT
--
-- PROBLEMA 4: Tabela não existe
--   SOLUÇÃO: Executar migrações
-- ============================================
