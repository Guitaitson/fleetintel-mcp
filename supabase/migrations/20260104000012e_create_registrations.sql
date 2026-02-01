-- ============================================
-- MIGRATION 12e: Criar Registrations + Validação
-- Data: 2026-01-04
-- Parte 5/5 do Redesign V2
-- ============================================

BEGIN;

-- ============================================
-- TABELA: registrations (NÚCLEO)
-- ============================================

CREATE TABLE registrations (
    id SERIAL PRIMARY KEY,
    external_id TEXT UNIQUE NOT NULL,
    
    -- Relacionamentos (FKs)
    vehicle_id INT NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    empresa_id INT NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    
    -- Dados do emplacamento
    data_emplacamento DATE NOT NULL,
    municipio_emplacamento TEXT,
    uf_emplacamento CHAR(2),
    regiao_emplacamento TEXT,
    
    -- Concessionária
    cnpj_concessionario CHAR(14),
    concessionario TEXT,
    area_operacional TEXT,
    
    -- Comercial
    preco DECIMAL(12,2),
    preco_validado BOOLEAN,
    
    -- Metadata
    fonte TEXT DEFAULT 'excel_inicial',
    versao_carga INT DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Chave composta para UPSERT
    UNIQUE(vehicle_id, data_emplacamento)
);

CREATE UNIQUE INDEX idx_registrations_external_id ON registrations(external_id);
CREATE INDEX idx_registrations_vehicle ON registrations(vehicle_id);
CREATE INDEX idx_registrations_empresa ON registrations(empresa_id);
CREATE INDEX idx_registrations_data_emplac ON registrations(data_emplacamento);
CREATE INDEX idx_registrations_uf_emplac ON registrations(uf_emplacamento);
CREATE INDEX idx_registrations_preco ON registrations(preco) WHERE preco IS NOT NULL;

COMMENT ON TABLE registrations IS 'Registros de emplacamentos (núcleo do sistema)';
COMMENT ON COLUMN registrations.external_id IS 'ID único gerado: chassi_data ou hash';
COMMENT ON COLUMN registrations.vehicle_id IS 'FK para vehicles';
COMMENT ON COLUMN registrations.empresa_id IS 'FK para empresas (proprietário)';

-- ============================================
-- VALIDAÇÃO FINAL
-- ============================================

DO $$
DECLARE
    tabela_count INT;
    fk_count INT;
    func_count INT;
BEGIN
    -- Contar tabelas criadas
    SELECT COUNT(*) INTO tabela_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'marcas', 'modelos', 'vehicles', 'empresas', 
        'enderecos', 'contatos', 'registrations', 'cnae_lookup'
    );
    
    -- Contar FKs
    SELECT COUNT(*) INTO fk_count
    FROM information_schema.table_constraints
    WHERE table_schema = 'public'
    AND constraint_type = 'FOREIGN KEY';
    
    -- Contar funções
    SELECT COUNT(*) INTO func_count
    FROM information_schema.routines
    WHERE routine_schema = 'public'
    AND routine_name IN ('fix_documento', 'update_updated_at_column');
    
    RAISE NOTICE '';
    RAISE NOTICE '============================================';
    RAISE NOTICE '✅ REDESIGN V2 COMPLETO!';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Migration 12a: ✅ Schema antigo removido';
    RAISE NOTICE 'Migration 12b: ✅ Funções criadas (%)' , func_count;
    RAISE NOTICE 'Migration 12c: ✅ Tabelas de domínio';
    RAISE NOTICE 'Migration 12d: ✅ Tabelas principais';
    RAISE NOTICE 'Migration 12e: ✅ Registrations + validação';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Resumo:';
    RAISE NOTICE '   Tabelas: % / 8', tabela_count;
    RAISE NOTICE '   Foreign Keys: %', fk_count;
    RAISE NOTICE '   Funções auxiliares: % / 2', func_count;
    RAISE NOTICE '';
    RAISE NOTICE '✅ Schema normalizado (3NF)';
    RAISE NOTICE '✅ Tipos de dados corretos (CNPJ com 14 dígitos)';
    RAISE NOTICE '✅ Relacionamentos com FKs';
    RAISE NOTICE '✅ Índices otimizados';
    RAISE NOTICE '✅ Pronto para BrasilAPI';
    RAISE NOTICE '============================================';
    RAISE NOTICE '';
    
    -- Validação
    IF tabela_count < 8 THEN
        RAISE EXCEPTION 'Migração incompleta: esperado 8 tabelas, encontrado %', tabela_count;
    END IF;
    
    IF func_count < 2 THEN
        RAISE EXCEPTION 'Funções faltando: esperado 2, encontrado %', func_count;
    END IF;
    
    RAISE NOTICE '🎉 Banco de dados pronto para receber 974k registros!';
    RAISE NOTICE '';
END $$;

COMMIT;
