-- Verificar se a tabela registrations existe antes de aplicar alterações
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'registrations') THEN
        -- Habilitar Row Level Security na tabela registrations
        ALTER TABLE registrations ENABLE ROW LEVEL SECURITY;

        -- Criar política de leitura pública para registrations
        CREATE POLICY "Enable public read access for registrations"
        ON registrations FOR SELECT
        USING (true);

        -- Recarregar schema do PostgREST para expor a tabela via API
        NOTIFY pgrst, 'reload schema';
    ELSE
        RAISE WARNING 'Tabela registrations não existe. Migração ignorada.';
    END IF;
END $$;
