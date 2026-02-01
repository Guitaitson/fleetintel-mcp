-- ============================================
-- MIGRAÇÃO 11: Criar tabela CNAE Lookup
-- Data: 2026-01-04
-- Objetivo: Tabela de referência para CNAEs (Classificação Nacional de Atividades Econômicas)
-- ============================================

BEGIN;

-- Criar tabela CNAE lookup
CREATE TABLE IF NOT EXISTS cnae_lookup (
    id SERIAL PRIMARY KEY,
    
    -- Hierarquia CNAE (5 níveis)
    secao TEXT,
    desc_secao TEXT,
    divisao TEXT,
    desc_divisao TEXT,
    grupo TEXT,
    desc_grupo TEXT,
    classe TEXT,
    desc_classe TEXT,
    subclasse TEXT UNIQUE NOT NULL,  -- Chave única (mais específico)
    
    -- Campos de enriquecimento
    subclasse_tratado TEXT,
    salesforce TEXT,
    denominacao TEXT,
    mercado_enderecavel TEXT,
    setor_addiante_v2 TEXT,
    atuacao TEXT,
    setor_addiante_agrupado TEXT,
    
    -- Metadados
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- ÍNDICES
-- ============================================

-- Índice único na subclasse (primary lookup key)
CREATE UNIQUE INDEX IF NOT EXISTS idx_cnae_subclasse 
  ON cnae_lookup(subclasse);

-- Índice na classe (lookup secundário)
CREATE INDEX IF NOT EXISTS idx_cnae_classe 
  ON cnae_lookup(classe);

-- Índice na seção (agregação top-level)
CREATE INDEX IF NOT EXISTS idx_cnae_secao 
  ON cnae_lookup(secao);

-- Índice na divisão
CREATE INDEX IF NOT EXISTS idx_cnae_divisao 
  ON cnae_lookup(divisao);

-- Índice para mercado endereçável
CREATE INDEX IF NOT EXISTS idx_cnae_mercado_enderecavel 
  ON cnae_lookup(mercado_enderecavel);

-- Índice para setor Addiante
CREATE INDEX IF NOT EXISTS idx_cnae_setor_addiante 
  ON cnae_lookup(setor_addiante_v2);

-- Índice GIN para busca textual na denominação
CREATE INDEX IF NOT EXISTS idx_cnae_denominacao_gin 
  ON cnae_lookup USING gin(to_tsvector('portuguese', denominacao));

-- ============================================
-- TRIGGER PARA UPDATED_AT
-- ============================================

CREATE TRIGGER update_cnae_lookup_updated_at
BEFORE UPDATE ON cnae_lookup
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- COMENTÁRIOS
-- ============================================

COMMENT ON TABLE cnae_lookup IS 'Tabela de referência CNAE - Classificação Nacional de Atividades Econômicas';

COMMENT ON COLUMN cnae_lookup.secao IS 'Código da seção (nível 1 - mais amplo)';
COMMENT ON COLUMN cnae_lookup.desc_secao IS 'Descrição da seção';
COMMENT ON COLUMN cnae_lookup.divisao IS 'Código da divisão (nível 2)';
COMMENT ON COLUMN cnae_lookup.desc_divisao IS 'Descrição da divisão';
COMMENT ON COLUMN cnae_lookup.grupo IS 'Código do grupo (nível 3)';
COMMENT ON COLUMN cnae_lookup.desc_grupo IS 'Descrição do grupo';
COMMENT ON COLUMN cnae_lookup.classe IS 'Código da classe (nível 4)';
COMMENT ON COLUMN cnae_lookup.desc_classe IS 'Descrição da classe';
COMMENT ON COLUMN cnae_lookup.subclasse IS 'Código da subclasse (nível 5 - mais específico) - CHAVE ÚNICA';
COMMENT ON COLUMN cnae_lookup.denominacao IS 'Denominação completa da atividade';
COMMENT ON COLUMN cnae_lookup.mercado_enderecavel IS 'Se o CNAE é relevante comercialmente';
COMMENT ON COLUMN cnae_lookup.setor_addiante_v2 IS 'Classificação Addiante do setor';
COMMENT ON COLUMN cnae_lookup.atuacao IS 'Tipo de atuação comercial';
COMMENT ON COLUMN cnae_lookup.setor_addiante_agrupado IS 'Setor Addiante agrupado';

-- ============================================
-- FUNÇÃO AUXILIAR: Buscar CNAE por código
-- ============================================

CREATE OR REPLACE FUNCTION get_cnae_info(p_cnae_code TEXT)
RETURNS TABLE (
    subclasse TEXT,
    denominacao TEXT,
    secao TEXT,
    desc_secao TEXT,
    setor_addiante TEXT,
    mercado_enderecavel TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.subclasse,
        c.denominacao,
        c.secao,
        c.desc_secao,
        c.setor_addiante_v2,
        c.mercado_enderecavel
    FROM cnae_lookup c
    WHERE c.subclasse = p_cnae_code
       OR c.classe = p_cnae_code
       OR c.grupo = p_cnae_code;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_cnae_info IS 'Busca informações de CNAE por código (subclasse, classe ou grupo)';

-- ============================================
-- VALIDAÇÃO
-- ============================================

DO $$
BEGIN
    RAISE NOTICE 'Tabela cnae_lookup criada com sucesso';
    RAISE NOTICE 'Total de índices criados: 7';
    RAISE NOTICE 'Função get_cnae_info() disponível para lookup';
END $$;

COMMIT;
