-- FleetIntel Trigram Extension Migration
-- Enable pg_trgm for fuzzy text search
-- Fallback for when pgvector is not available
-- Generated: 2026-02-06

-- Enable pg_trgm extension (more commonly available than pgvector)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Verify installation
SELECT extname, extversion FROM pg_extension WHERE extname = 'pg_trgm';

-- Expected output:
-- | extname | extversion |
-- |---------|------------|
-- | pg_trgm | 1.6        |

-- Create indexes for fuzzy search
-- These indexes enable fast ILIKE queries with wildcards
CREATE INDEX IF NOT EXISTS idx_empresas_razao_social_trgm 
ON empresas USING gin (razao_social gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_empresas_nome_fantasia_trgm 
ON empresas USING gin (nome_fantasia gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_empresas_segmento_cliente_trgm 
ON empresas USING gin (segmento_cliente gin_trgm_ops);

-- Create similarity function
CREATE OR REPLACE FUNCTION fleetintel_similarity(
    text1 TEXT,
    text2 TEXT
)
RETURNS FLOAT
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN similarity(text1, text2);
END;
$$;

-- Create ranked search function
CREATE OR REPLACE FUNCTION fleetintel_search_empresas_fuzzy(
    search_query TEXT,
    match_count INT DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    empresa_id BIGINT,
    razao_social TEXT,
    nome_fantasia TEXT,
    segmento_cliente TEXT,
    similarity_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id AS empresa_id,
        e.razao_social,
        e.nome_fantasia,
        e.segmento_cliente,
        GREATEST(
            similarity(e.razao_social, search_query),
            similarity(e.nome_fantasia, search_query),
            similarity(e.segmento_cliente, search_query)
        ) AS similarity_score
    FROM empresas e
    WHERE GREATEST(
            similarity(e.razao_social, search_query),
            similarity(e.nome_fantasia, search_query),
            similarity(e.segmento_cliente, search_query)
        ) > similarity_threshold
    ORDER BY similarity_score DESC
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION fleetintel_search_empresas_fuzzy IS 
'Fuzzy search using pg_trgm similarity.
 Params: search_query (text), match_count (default 10), similarity_threshold (default 0.3)
 Returns: empresas ranked by trigram similarity';

-- Create hybrid search (combines multiple techniques)
CREATE OR REPLACE FUNCTION fleetintel_search_empresas_hybrid(
    search_query TEXT,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    empresa_id BIGINT,
    razao_social TEXT,
    nome_fantasia TEXT,
    segmento_cliente TEXT,
    match_type TEXT,
    rank_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id AS empresa_id,
        e.razao_social,
        e.nome_fantasia,
        e.segmento_cliente,
        CASE 
            WHEN e.razao_social ILIKE search_query THEN 'exact'
            WHEN e.razao_social ILIKE '%' || search_query || '%' THEN 'contains'
            ELSE 'fuzzy'
        END AS match_type,
        CASE 
            WHEN e.razao_social ILIKE search_query THEN 1.0
            WHEN e.razao_social ILIKE '%' || search_query || '%' THEN 0.9
            ELSE COALESCE(similarity(e.razao_social, search_query), 0)
        END AS rank_score
    FROM empresas e
    WHERE e.razao_social ILIKE '%' || search_query || '%'
       OR e.nome_fantasia ILIKE '%' || search_query || '%'
       OR similarity(e.razao_social, search_query) > 0.3
    ORDER BY rank_score DESC
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION fleetintel_search_empresas_hybrid IS 
'Hybrid search combining exact, contains, and fuzzy matching.
 Params: search_query (text), match_count (default 10)
 Returns: empresas ranked by match quality';

-- Example queries for testing:
-- SELECT * FROM fleetintel_search_empresas_fuzzy('transportadora', 10, 0.3);
-- SELECT * FROM fleetintel_search_empresas_huzzy('empresa de logistica', 10);
