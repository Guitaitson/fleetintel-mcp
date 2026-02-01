-- ============================================
-- CORREÇÃO DE PERMISSÕES POSTGREST
-- ============================================
-- Esta migração corrige a exposição de tabelas via API REST do Supabase

-- 1. CONFIGURAR SCHEMA NO ROLE AUTHENTICATOR
-- O PostgREST usa o role authenticator para determinar quais schemas expor
ALTER ROLE authenticator SET pgrst.db_schemas = 'public, storage';

-- 2. GARANTIR PERMISSÕES DE SCHEMA
-- Os roles anon e authenticated precisam de USAGE no schema public
GRANT USAGE ON SCHEMA public TO anon, authenticated;

-- 3. GARANTIR PERMISSÕES NA TABELA REGISTRATIONS
-- Permitir SELECT para roles anon e authenticated
GRANT SELECT ON public.registrations TO anon, authenticated;

-- 4. GARANTIR PERMISSÕES NA TABELA _MIGRATIONS
-- Útil para testes e verificação
GRANT SELECT ON public._migrations TO anon, authenticated;

-- 5. VERIFICAR SE RLS JÁ ESTÁ HABILITADO (da migração anterior)
-- Se não estiver, habilitar agora
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE tablename = 'registrations' 
        AND rowsecurity = true
    ) THEN
        ALTER TABLE public.registrations ENABLE ROW LEVEL SECURITY;
    END IF;
END $$;

-- 6. VERIFICAR SE POLICY JÁ EXISTE (da migração anterior)
-- Se não existir, criar agora
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'registrations' 
        AND policyname = 'Enable public read access for registrations'
    ) THEN
        CREATE POLICY "Enable public read access for registrations"
        ON public.registrations FOR SELECT
        USING (true);
    END IF;
END $$;

-- 7. ADICIONAR POLICY PARA _MIGRATIONS TAMBÉM
DO $$
BEGIN
    -- Habilitar RLS em _migrations
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE tablename = '_migrations' 
        AND rowsecurity = true
    ) THEN
        ALTER TABLE public._migrations ENABLE ROW LEVEL SECURITY;
    END IF;
    
    -- Criar policy para leitura pública
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = '_migrations' 
        AND policyname = 'Enable public read access for migrations'
    ) THEN
        CREATE POLICY "Enable public read access for migrations"
        ON public._migrations FOR SELECT
        USING (true);
    END IF;
END $$;

-- 8. RECARREGAR SCHEMA DO POSTGREST
-- Força o PostgREST a recarregar o cache de schema
NOTIFY pgrst, 'reload schema';

-- ============================================
-- COMENTÁRIOS E DOCUMENTAÇÃO
-- ============================================

COMMENT ON TABLE public.registrations IS 
'Tabela central de registros de veículos (600k+) - Exposta via API REST';

COMMENT ON TABLE public._migrations IS 
'Controle de migrações aplicadas - Exposta via API REST para verificação';
