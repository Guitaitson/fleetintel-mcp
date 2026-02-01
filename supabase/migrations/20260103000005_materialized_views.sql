-- View materializada para estatísticas por estado
CREATE MATERIALIZED VIEW IF NOT EXISTS estatisticas_por_estado AS
SELECT
    uf,
    COUNT(*) AS total_veiculos,
    COUNT(DISTINCT marca) AS marcas_distintas,
    COUNT(DISTINCT modelo) AS modelos_distintas,
    MAX(ano_fabricacao) AS max_ano_fabricacao,
    MIN(ano_fabricacao) AS min_ano_fabricacao
FROM registrations
GROUP BY uf;

-- View materializada para estatísticas por município
CREATE MATERIALIZED VIEW IF NOT EXISTS estatisticas_por_municipio AS
SELECT
    municipio,
    uf,
    COUNT(*) AS total_veiculos,
    ROUND(AVG(ano_fabricacao), 2) AS media_ano_fabricacao
FROM registrations
GROUP BY municipio, uf;

-- View materializada para estatísticas por categoria
CREATE MATERIALIZED VIEW IF NOT EXISTS estatisticas_por_categoria AS
SELECT
    categoria,
    COUNT(*) AS total_veiculos,
    ROUND(AVG(ano_fabricacao), 2) AS media_ano_fabricacao
FROM registrations
GROUP BY categoria;

-- Comentários
COMMENT ON MATERIALIZED VIEW estatisticas_por_estado IS 'Estatísticas agregadas por estado';
COMMENT ON MATERIALIZED VIEW estatisticas_por_municipio IS 'Estatísticas agregadas por município';
COMMENT ON MATERIALIZED VIEW estatisticas_por_categoria IS 'Estatísticas agregadas por categoria de veículo';

-- Índices para atualização eficiente
CREATE UNIQUE INDEX IF NOT EXISTS idx_estatisticas_por_estado_uf ON estatisticas_por_estado (uf);
CREATE UNIQUE INDEX IF NOT EXISTS idx_estatisticas_por_municipio_municipio_uf ON estatisticas_por_municipio (municipio, uf);
CREATE UNIQUE INDEX IF NOT EXISTS idx_estatisticas_por_categoria_categoria ON estatisticas_por_categoria (categoria);

-- Função para refresh concorrente
CREATE OR REPLACE FUNCTION refresh_materialized_views_concurrently()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY estatisticas_por_estado;
    REFRESH MATERIALIZED VIEW CONCURRENTLY estatisticas_por_municipio;
    REFRESH MATERIALIZED VIEW CONCURRENTLY estatisticas_por_categoria;
END;
$$ LANGUAGE plpgsql;
