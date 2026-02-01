-- ============================================
-- MIGRATION 12c: Criar Tabelas de Domínio
-- Data: 2026-01-04
-- Parte 3/5 do Redesign V2
-- ============================================

BEGIN;

-- Tabela: marcas
CREATE TABLE marcas (
    id SERIAL PRIMARY KEY,
    nome TEXT UNIQUE NOT NULL,
    nome_normalizado TEXT GENERATED ALWAYS AS (UPPER(TRIM(nome))) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_marcas_nome_normalizado ON marcas(nome_normalizado);

COMMENT ON TABLE marcas IS 'Tabela de domínio: Marcas de veículos';
COMMENT ON COLUMN marcas.nome_normalizado IS 'Nome normalizado para busca (uppercase, trimmed)';

-- Tabela: modelos
CREATE TABLE modelos (
    id SERIAL PRIMARY KEY,
    marca_id INT NOT NULL REFERENCES marcas(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    cod_modelo TEXT,
    segmento TEXT,
    subsegmento TEXT,
    grupo_modelo TEXT,
    tracao TEXT,
    cilindrada TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(marca_id, nome)
);

CREATE INDEX idx_modelos_marca ON modelos(marca_id);
CREATE INDEX idx_modelos_nome ON modelos(nome);
CREATE INDEX idx_modelos_segmento ON modelos(segmento);

COMMENT ON TABLE modelos IS 'Tabela de domínio: Modelos de veículos por marca';

-- Confirmar criação
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 12c: Tabelas de domínio criadas';
    RAISE NOTICE '   - marcas (com nome_normalizado)';
    RAISE NOTICE '   - modelos (FK para marcas)';
END $$;

COMMIT;
