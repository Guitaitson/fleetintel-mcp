-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Para busca textual

-- Tabela principal: registrations
CREATE TABLE IF NOT EXISTS registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identificadores externos
    external_id TEXT UNIQUE NOT NULL,
    
    -- Dados do veículo
    placa TEXT NOT NULL,
    renavam TEXT,
    chassi TEXT,
    marca TEXT,
    modelo TEXT,
    ano_fabricacao INTEGER,
    ano_modelo INTEGER,
    cor TEXT,
    categoria TEXT,
    
    -- Localização
    municipio TEXT,
    uf CHAR(2),
    
    -- Status
    situacao TEXT,
    restricao TEXT,
    
    -- Timestamps
    data_registro TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Origem
    fonte TEXT DEFAULT 'excel_inicial',
    versao_carga INTEGER DEFAULT 1,
    
    -- Metadados
    raw_data JSONB, -- JSON original para auditoria
    
    -- Constraints
    CONSTRAINT registrations_placa_valida CHECK (placa ~* '^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$')
);

-- Comentários
COMMENT ON TABLE registrations IS 'Tabela central de registros de veículos (600k+)';
COMMENT ON COLUMN registrations.external_id IS 'Chave única da fonte externa';
COMMENT ON COLUMN registrations.raw_data IS 'JSON original para rastreabilidade';

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_registrations_updated_at
BEFORE UPDATE ON registrations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
