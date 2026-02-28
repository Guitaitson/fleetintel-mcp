-- =============================================================================
-- FLEETINTEL MCP - SCHEMA COMPLETO
-- Executado automaticamente na inicializacao do container PostgreSQL
-- Indices sao criados SEPARADAMENTE em create_indexes.sql (pos-carga ETL)
-- =============================================================================

-- Extensoes
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- TABELAS DE DOMINIO
-- =============================================================================

CREATE TABLE IF NOT EXISTS marcas (
    id SERIAL PRIMARY KEY,
    nome TEXT UNIQUE NOT NULL,
    nome_normalizado TEXT GENERATED ALWAYS AS (UPPER(TRIM(nome))) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS modelos (
    id SERIAL PRIMARY KEY,
    marca_id INT NOT NULL REFERENCES marcas(id),
    nome TEXT NOT NULL,
    segmento TEXT,
    subsegmento TEXT,
    tracao TEXT,
    cilindrada TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(marca_id, nome)
);

-- =============================================================================
-- TABELA DE LOOKUP CNAE
-- =============================================================================

CREATE TABLE IF NOT EXISTS cnae_lookup (
    id SERIAL PRIMARY KEY,
    codigo TEXT UNIQUE NOT NULL,
    descricao TEXT NOT NULL,
    secao TEXT,
    divisao TEXT,
    grupo TEXT,
    classe TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- TABELA PRINCIPAL: VEICULOS
-- =============================================================================

CREATE TABLE IF NOT EXISTS vehicles (
    id SERIAL PRIMARY KEY,
    chassi VARCHAR(25) UNIQUE NOT NULL,
    placa CHAR(7),
    marca_id INT REFERENCES marcas(id),
    modelo_id INT REFERENCES modelos(id),
    ano_fabricacao INT,
    ano_modelo INT,
    cor TEXT,
    categoria TEXT,
    -- Colunas desnormalizadas para evitar JOINs em queries frequentes
    marca_nome TEXT,
    modelo_nome TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- TABELA: EMPRESAS (PROPRIETARIOS)
-- =============================================================================

CREATE TABLE IF NOT EXISTS empresas (
    id SERIAL PRIMARY KEY,
    cnpj CHAR(14) UNIQUE NOT NULL,
    -- Dados basicos
    razao_social TEXT,
    nome_fantasia TEXT,
    tipo_proprietario TEXT,
    -- Classificacao
    cnae_id INT REFERENCES cnae_lookup(id),
    porte TEXT,
    natureza_juridica TEXT,
    codigo_natureza_juridica INT,
    -- Status
    situacao_cadastral TEXT,
    data_abertura DATE,
    idade_empresa_dias INT,
    faixa_idade_empresa TEXT,
    -- Segmentacao de frota
    segmento_cliente TEXT,
    grupo_locadora TEXT,
    -- Enriquecimento BrasilAPI (preenchido pelo job de enriquecimento)
    brasilapi_qsa JSONB,
    brasilapi_cnaes_secundarios JSONB,
    brasilapi_raw JSONB,
    brasilapi_status TEXT DEFAULT 'pending',
    brasilapi_updated_at TIMESTAMPTZ,
    brasilapi_error TEXT,
    -- Metadata
    source TEXT DEFAULT 'excel',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- TABELA: ENDERECOS (1:1 com empresas)
-- =============================================================================

CREATE TABLE IF NOT EXISTS enderecos (
    id SERIAL PRIMARY KEY,
    empresa_id INT UNIQUE NOT NULL REFERENCES empresas(id),
    cep CHAR(8),
    logradouro TEXT,
    numero TEXT,
    complemento TEXT,
    bairro TEXT,
    cidade TEXT,
    uf CHAR(2),
    codigo_municipio_ibge INT,
    -- Geolocalizacao (enriquecido via BrasilAPI CEP V2)
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    -- Enriquecimento BrasilAPI
    brasilapi_raw JSONB,
    brasilapi_status TEXT DEFAULT 'pending',
    brasilapi_updated_at TIMESTAMPTZ,
    brasilapi_error TEXT,
    -- Metadata
    source TEXT DEFAULT 'excel',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- TABELA: CONTATOS (1:1 com empresas)
-- =============================================================================

CREATE TABLE IF NOT EXISTS contatos (
    id SERIAL PRIMARY KEY,
    empresa_id INT UNIQUE NOT NULL REFERENCES empresas(id),
    telefones TEXT[],
    celulares TEXT[],
    email TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- TABELA CENTRAL: REGISTRATIONS (EMPLACAMENTOS)
-- =============================================================================

CREATE TABLE IF NOT EXISTS registrations (
    id SERIAL PRIMARY KEY,
    external_id TEXT UNIQUE NOT NULL,
    -- Relacionamentos
    vehicle_id INT NOT NULL REFERENCES vehicles(id),
    empresa_id INT NOT NULL REFERENCES empresas(id),
    -- Dados do emplacamento
    data_emplacamento DATE NOT NULL,
    municipio_emplacamento TEXT,
    uf_emplacamento CHAR(2),
    regiao_emplacamento TEXT,
    -- Concessionaria
    cnpj_concessionario CHAR(14),
    concessionario TEXT,
    area_operacional TEXT,
    -- Comercial
    preco DECIMAL(12, 2),
    preco_validado BOOLEAN,
    -- Metadata
    fonte TEXT DEFAULT 'excel_inicial',
    versao_carga INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    -- Chave composta para upsert
    UNIQUE(vehicle_id, data_emplacamento)
);

-- =============================================================================
-- FUNCAO UTILITARIA: Normalizar documentos (CNPJ, CPF, CEP)
-- =============================================================================

CREATE OR REPLACE FUNCTION fix_documento(doc TEXT, tamanho INT)
RETURNS TEXT AS $$
BEGIN
    IF doc IS NULL OR doc = '' THEN
        RETURN NULL;
    END IF;
    doc := regexp_replace(doc, '\D', '', 'g');
    IF doc = '' THEN
        RETURN NULL;
    END IF;
    RETURN lpad(doc, tamanho, '0');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- NOTA: Execute scripts/create_indexes.sql APOS a carga ETL completa
-- =============================================================================
