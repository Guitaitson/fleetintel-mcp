-- Tabela de estados (UF)
CREATE TABLE IF NOT EXISTS estados (
    uf CHAR(2) PRIMARY KEY,
    nome TEXT NOT NULL
);

-- Tabela de municípios
CREATE TABLE IF NOT EXISTS municipios (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    uf CHAR(2) REFERENCES estados(uf),
    codigo_ibge INTEGER UNIQUE
);

-- Tabela de categorias de veículos
CREATE TABLE IF NOT EXISTS categorias_veiculo (
    id SERIAL PRIMARY KEY,
    nome TEXT UNIQUE NOT NULL,
    descricao TEXT
);

-- Tabela de marcas
CREATE TABLE IF NOT EXISTS marcas (
    id SERIAL PRIMARY KEY,
    nome TEXT UNIQUE NOT NULL
);

-- Tabela de modelos
CREATE TABLE IF NOT EXISTS modelos (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    marca_id INTEGER REFERENCES marcas(id),
    UNIQUE (nome, marca_id)
);

-- Comentários
COMMENT ON TABLE estados IS 'Tabela auxiliar de estados brasileiros';
COMMENT ON TABLE municipios IS 'Tabela auxiliar de municípios brasileiros';
COMMENT ON TABLE categorias_veiculo IS 'Categorias de veículos (passeio, carga, etc.)';
COMMENT ON TABLE marcas IS 'Marcas de veículos';
COMMENT ON TABLE modelos IS 'Modelos de veículos por marca';

-- Adicionar FK para tabela principal
ALTER TABLE registrations
ADD COLUMN IF NOT EXISTS municipio_id INTEGER REFERENCES municipios(id),
ADD COLUMN IF NOT EXISTS categoria_id INTEGER REFERENCES categorias_veiculo(id),
ADD COLUMN IF NOT EXISTS marca_id INTEGER REFERENCES marcas(id),
ADD COLUMN IF NOT EXISTS modelo_id INTEGER REFERENCES modelos(id);
