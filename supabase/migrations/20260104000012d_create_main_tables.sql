-- ============================================
-- MIGRATION 12d: Criar Tabelas Principais
-- Data: 2026-01-04
-- Parte 4/5 do Redesign V2
-- ============================================

BEGIN;

-- ============================================
-- TABELA: vehicles
-- ============================================

CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    chassi TEXT UNIQUE NOT NULL,
    placa TEXT,
    marca_id INT REFERENCES marcas(id),
    modelo_id INT REFERENCES modelos(id),
    ano_fabricacao INT,
    ano_modelo INT,
    cor TEXT,
    categoria TEXT,
    
    -- Denormalização estratégica (evita JOINs)
    marca_nome TEXT,
    modelo_nome TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_vehicles_chassi ON vehicles(chassi);
CREATE INDEX idx_vehicles_placa ON vehicles(placa);
CREATE INDEX idx_vehicles_marca ON vehicles(marca_id);
CREATE INDEX idx_vehicles_modelo ON vehicles(modelo_id);

CREATE TRIGGER update_vehicles_updated_at
BEFORE UPDATE ON vehicles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE vehicles IS 'Dados dos veículos (imutáveis)';
COMMENT ON COLUMN vehicles.marca_nome IS 'Denormalizado para performance';
COMMENT ON COLUMN vehicles.modelo_nome IS 'Denormalizado para performance';

-- ============================================
-- TABELA: empresas
-- ============================================

CREATE TABLE empresas (
    id SERIAL PRIMARY KEY,
    cnpj CHAR(14) UNIQUE NOT NULL,
    
    -- Dados básicos
    razao_social TEXT,
    nome_fantasia TEXT,
    tipo_proprietario TEXT,
    
    -- Classificação
    cnae_id INT REFERENCES cnae_lookup(id),
    porte TEXT,
    natureza_juridica TEXT,
    codigo_natureza_juridica INT,
    
    -- Status
    situacao_cadastral TEXT,
    data_abertura DATE,
    idade_empresa_dias INT,
    faixa_idade_empresa TEXT,
    
    -- Segmentação
    segmento_cliente TEXT,
    grupo_locadora TEXT,
    
    -- Enriquecimento BrasilAPI
    brasilapi_qsa JSONB,
    brasilapi_cnaes_secundarios JSONB,
    brasilapi_raw JSONB,
    brasilapi_status TEXT CHECK (brasilapi_status IN ('pending', 'success', 'error', NULL)),
    brasilapi_updated_at TIMESTAMP WITH TIME ZONE,
    brasilapi_error TEXT,
    
    -- Metadata
    source TEXT DEFAULT 'excel',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_empresas_cnpj ON empresas(cnpj);
CREATE INDEX idx_empresas_cnae ON empresas(cnae_id);
CREATE INDEX idx_empresas_brasilapi_status ON empresas(brasilapi_status) 
  WHERE brasilapi_status IS NOT NULL;
CREATE INDEX idx_empresas_razao_social_trgm ON empresas USING gin(razao_social gin_trgm_ops);

CREATE TRIGGER update_empresas_updated_at
BEFORE UPDATE ON empresas
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE empresas IS 'Empresas proprietárias (CNPJ) com integração BrasilAPI';
COMMENT ON COLUMN empresas.brasilapi_status IS 'Status do enriquecimento: pending|success|error';
COMMENT ON COLUMN empresas.brasilapi_qsa IS 'Quadro Societário e Administrativo (BrasilAPI)';

-- ============================================
-- TABELA: enderecos
-- ============================================

CREATE TABLE enderecos (
    id SERIAL PRIMARY KEY,
    empresa_id INT UNIQUE NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    
    -- Endereço
    cep CHAR(8),
    logradouro TEXT,
    numero TEXT,
    complemento TEXT,
    bairro TEXT,
    cidade TEXT,
    uf CHAR(2),
    codigo_municipio_ibge INT,
    
    -- Geolocalização (BrasilAPI CEP V2)
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Enriquecimento BrasilAPI
    brasilapi_raw JSONB,
    brasilapi_status TEXT CHECK (brasilapi_status IN ('pending', 'success', 'error', NULL)),
    brasilapi_updated_at TIMESTAMP WITH TIME ZONE,
    brasilapi_error TEXT,
    
    -- Metadata
    source TEXT DEFAULT 'excel',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_enderecos_empresa ON enderecos(empresa_id);
CREATE INDEX idx_enderecos_cep ON enderecos(cep);
CREATE INDEX idx_enderecos_cidade_uf ON enderecos(cidade, uf);
CREATE INDEX idx_enderecos_brasilapi_status ON enderecos(brasilapi_status) 
  WHERE brasilapi_status IS NOT NULL;
CREATE INDEX idx_enderecos_location ON enderecos(latitude, longitude) 
  WHERE latitude IS NOT NULL;

COMMENT ON TABLE enderecos IS 'Endereços de empresas com geolocalização (BrasilAPI CEP V2)';
COMMENT ON COLUMN enderecos.latitude IS 'Latitude (BrasilAPI CEP V2)';
COMMENT ON COLUMN enderecos.longitude IS 'Longitude (BrasilAPI CEP V2)';

-- ============================================
-- TABELA: contatos
-- ============================================

CREATE TABLE contatos (
    id SERIAL PRIMARY KEY,
    empresa_id INT UNIQUE NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    
    telefones TEXT[],
    celulares TEXT[],
    email TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_contatos_empresa ON contatos(empresa_id);
CREATE INDEX idx_contatos_telefones_gin ON contatos USING gin(telefones);

CREATE TRIGGER update_contatos_updated_at
BEFORE UPDATE ON contatos
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE contatos IS 'Contatos de empresas (telefones, celulares, email)';
COMMENT ON COLUMN contatos.telefones IS 'Array de telefones fixos';
COMMENT ON COLUMN contatos.celulares IS 'Array de celulares';

-- Confirmar criação
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 12d: Tabelas principais criadas';
    RAISE NOTICE '   - vehicles (com FKs para marcas/modelos)';
    RAISE NOTICE '   - empresas (com campos BrasilAPI)';
    RAISE NOTICE '   - enderecos (com geolocalização)';
    RAISE NOTICE '   - contatos (telefones/celulares/email)';
END $$;

COMMIT;
