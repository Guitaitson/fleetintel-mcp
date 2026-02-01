-- Criar tabela temporária para dados deduplicados
CREATE TEMP TABLE deduped_registrations AS
SELECT DISTINCT ON (external_id) *
FROM registrations
ORDER BY external_id, created_at DESC;

-- Limpar tabela original
TRUNCATE TABLE registrations;

-- Reinserir dados deduplicados
INSERT INTO registrations
SELECT * FROM deduped_registrations;

-- Criar índice único para evitar duplicatas futuras
CREATE UNIQUE INDEX IF NOT EXISTS registrations_external_id_idx
ON registrations (external_id);

-- Comentário sobre índice
COMMENT ON INDEX registrations_external_id_idx IS 'Garante unicidade de external_id';

-- Função para UPSERT
CREATE OR REPLACE FUNCTION upsert_registration_simple(
    p_external_id TEXT,
    p_data JSONB
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO registrations (external_id, raw_data)
    VALUES (p_external_id, p_data)
    ON CONFLICT (external_id) DO UPDATE
    SET raw_data = EXCLUDED.raw_data,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;
