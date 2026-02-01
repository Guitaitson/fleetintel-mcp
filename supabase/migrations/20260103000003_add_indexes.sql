-- Índices para consultas frequentes
CREATE INDEX IF NOT EXISTS registrations_placa_idx ON registrations (placa);
CREATE INDEX IF NOT EXISTS registrations_renavam_idx ON registrations (renavam);
CREATE INDEX IF NOT EXISTS registrations_chassi_idx ON registrations (chassi);
CREATE INDEX IF NOT EXISTS registrations_uf_idx ON registrations (uf);
CREATE INDEX IF NOT EXISTS registrations_municipio_idx ON registrations (municipio);
CREATE INDEX IF NOT EXISTS registrations_situacao_idx ON registrations (situacao);

-- Índice GIN para busca textual em JSONB
CREATE INDEX IF NOT EXISTS registrations_raw_data_gin_idx ON registrations USING GIN (raw_data);

-- Índice composto para consultas combinadas
CREATE INDEX IF NOT EXISTS registrations_placa_uf_idx ON registrations (placa, uf);

-- Comentários sobre índices
COMMENT ON INDEX registrations_placa_idx IS 'Acelera buscas por placa';
COMMENT ON INDEX registrations_renavam_idx IS 'Acelera buscas por renavam';
COMMENT ON INDEX registrations_chassi_idx IS 'Acelera buscas por chassi';
COMMENT ON INDEX registrations_uf_idx IS 'Acelera buscas por UF';
COMMENT ON INDEX registrations_municipio_idx IS 'Acelera buscas por município';
COMMENT ON INDEX registrations_situacao_idx IS 'Acelera buscas por situação';
COMMENT ON INDEX registrations_raw_data_gin_idx IS 'Índice GIN para busca em JSONB';
COMMENT ON INDEX registrations_placa_uf_idx IS 'Índice composto para consultas combinadas';
