-- ============================================
-- MIGRATION 12a: DROP Schema Antigo
-- Data: 2026-01-04
-- Parte 1/5 do Redesign V2
-- ============================================

BEGIN;

-- Dropar tabelas antigas (em ordem reversa de dependências)
DROP TABLE IF EXISTS registrations CASCADE;
DROP TABLE IF EXISTS estados CASCADE;
DROP TABLE IF EXISTS municipios CASCADE;
DROP TABLE IF EXISTS categorias_veiculo CASCADE;
DROP TABLE IF EXISTS marcas CASCADE;
DROP TABLE IF EXISTS modelos CASCADE;

-- Dropar views materializadas antigas
DROP MATERIALIZED VIEW IF EXISTS registration_summary CASCADE;
DROP MATERIALIZED VIEW IF EXISTS monthly_stats CASCADE;
DROP MATERIALIZED VIEW IF EXISTS estatisticas_por_estado CASCADE;
DROP MATERIALIZED VIEW IF EXISTS estatisticas_por_municipio CASCADE;
DROP MATERIALIZED VIEW IF EXISTS estatisticas_por_categoria CASCADE;

-- Dropar funções antigas
DROP FUNCTION IF EXISTS refresh_materialized_views_concurrently() CASCADE;
DROP FUNCTION IF EXISTS upsert_registration CASCADE;
DROP FUNCTION IF EXISTS upsert_registrations_batch CASCADE;
DROP FUNCTION IF EXISTS get_cnae_info CASCADE;

-- Confirmar remoção
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 12a: Schema antigo removido com sucesso';
END $$;

COMMIT;
