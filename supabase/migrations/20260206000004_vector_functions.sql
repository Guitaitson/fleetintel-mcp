-- FleetIntel Vector Similarity Search Functions
-- SQL functions for hybrid and vector search
-- Generated: 2026-02-06

-- ============================================
-- Pure Vector Search Function
-- ============================================

CREATE OR REPLACE FUNCTION fleetintel_search_empresas(
    query_embedding vector(768),
    match_count INT DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.5
)
RETURNS TABLE (
    empresa_id BIGINT,
    razao_social TEXT,
    nome_fantasia TEXT,
    segmento_cliente TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ee.empresa_id,
        e.razao_social,
        e.nome_fantasia,
        e.segmento_cliente,
        1 - (ee.embedding <=> query_embedding) AS similarity
    FROM empresa_embeddings ee
    JOIN empresas e ON e.id = ee.empresa_id
    WHERE 1 - (ee.embedding <=> query_embedding) > similarity_threshold
    ORDER BY ee.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION fleetintel_search_empresas IS 
'Search empresas using pure vector cosine similarity. 
 Params: query_embedding (768-dim), match_count (default 10), similarity_threshold (default 0.5)
 Returns: empresas ranked by cosine similarity';

-- ============================================
-- Hybrid Search Function (Vector + Keyword)
-- ============================================

CREATE OR REPLACE FUNCTION fleetintel_search_empresas_hybrid(
    query_embedding vector(768),
    match_count INT DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.5,
    keyword_weight FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    empresa_id BIGINT,
    razao_social TEXT,
    nome_fantasia TEXT,
    segmento_cliente TEXT,
    similarity FLOAT,
    search_type TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT 
            ee.empresa_id,
            ee.search_content,
            1 - (ee.embedding <=> query_embedding) AS vector_sim
        FROM empresa_embeddings ee
        WHERE 1 - (ee.embedding <=> query_embedding) > similarity_threshold
    ),
    keyword_results AS (
        SELECT 
            ee.empresa_id,
            CASE 
                WHEN e.razao_social ILIKE '%' || (SELECT split_part(ee.search_content, ' | ', 1)) || '%' THEN 1.0
                WHEN e.nome_fantasia ILIKE '%' || (SELECT split_part(ee.search_content, ' | ', 1)) || '%' THEN 0.9
                ELSE 0.5
            END AS keyword_sim
        FROM empresa_embeddings ee
        JOIN empresas e ON e.id = ee.empresa_id
        WHERE e.razao_social ILIKE '%' || (SELECT split_part(ee.search_content, ' | ', 1)) || '%'
           OR e.nome_fantasia ILIKE '%' || (SELECT split_part(ee.search_content, ' | ', 1)) || '%'
    )
    SELECT 
        e.id AS empresa_id,
        e.razao_social,
        e.nome_fantasia,
        e.segmento_cliente,
        COALESCE(
            (1 - keyword_weight) * v.vector_sim + keyword_weight * COALESCE(k.keyword_sim, 0.5),
            (1 - keyword_weight) * v.vector_sim
        ) AS similarity,
        CASE 
            WHEN k.keyword_sim IS NOT NULL THEN 'hybrid'
            ELSE 'vector'
        END AS search_type
    FROM empresas e
    LEFT JOIN vector_results v ON v.empresa_id = e.id
    LEFT JOIN keyword_results k ON k.empresa_id = e.id
    WHERE v.vector_sim IS NOT NULL
       OR k.keyword_sim IS NOT NULL
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION fleetintel_search_empresas_hybrid IS 
'Search empresas using hybrid approach (vector + keyword).
 Params: query_embedding, match_count, similarity_threshold, keyword_weight
 Returns: empresas ranked by combined score';

-- ============================================
-- Utility Functions
-- ============================================

-- Get embedding for a single empresa
CREATE OR REPLACE FUNCTION fleetintel_get_empresa_embedding(
    p_empresa_id BIGINT
)
RETURNS TABLE (
    empresa_id BIGINT,
    embedding vector(768),
    search_content TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ee.empresa_id,
        ee.embedding,
        ee.search_content
    FROM empresa_embeddings ee
    WHERE ee.empresa_id = p_empresa_id;
END;
$$;

-- Count empresas with embeddings
CREATE OR REPLACE FUNCTION fleetintel_count_empresa_embeddings()
RETURNS TABLE (
    total_empresas BIGINT,
    embedded_count BIGINT,
    coverage_percent FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM empresas) AS total_empresas,
        (SELECT COUNT(*) FROM empresa_embeddings) AS embedded_count,
        CASE 
            WHEN (SELECT COUNT(*) FROM empresas) > 0 
            THEN (SELECT COUNT(*) FROM empresa_embeddings)::FLOAT / (SELECT COUNT(*) FROM empresas) * 100
            ELSE 0
        END AS coverage_percent;
END;
$$;

-- ============================================
-- Test Queries (for verification)
-- ============================================

-- Test 1: Verify pgvector is working
-- SELECT 'vector test' AS test, [1.0, 2.0, 3.0]::vector AS embedding;

-- Test 2: Check function exists
-- SELECT routine_name FROM information_schema.routines 
-- WHERE routine_name LIKE 'fleetintel_search%';
