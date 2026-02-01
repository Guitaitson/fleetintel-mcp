-- ============================================
-- MIGRATION 12b: Criar Funções Auxiliares
-- Data: 2026-01-04
-- Parte 2/5 do Redesign V2
-- ============================================

BEGIN;

-- Função para corrigir documentos (CNPJ, CEP, CNAE)
CREATE OR REPLACE FUNCTION fix_documento(doc TEXT, tamanho INT) 
RETURNS TEXT AS $$
BEGIN
    IF doc IS NULL OR doc = '' THEN
        RETURN NULL;
    END IF;
    
    -- Remove tudo que não é dígito
    doc := regexp_replace(doc, '\D', '', 'g');
    
    -- Se vazio após limpeza, retorna NULL
    IF doc = '' THEN
        RETURN NULL;
    END IF;
    
    -- Preenche zeros à esquerda
    RETURN lpad(doc, tamanho, '0');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION fix_documento IS 'Corrige documentos removendo formatação e preenchendo zeros à esquerda';

-- Trigger genérico para updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Confirmar criação
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 12b: Funções auxiliares criadas';
    RAISE NOTICE '   - fix_documento(doc TEXT, tamanho INT)';
    RAISE NOTICE '   - update_updated_at_column()';
END $$;

COMMIT;
