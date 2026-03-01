-- FleetIntel Empresa Embeddings Table
-- Store vector embeddings for semantic search
-- Generated: 2026-02-06

-- Create empresa_embeddings table with pgvector
CREATE TABLE IF NOT EXISTS empresa_embeddings (
    id BIGSERIAL PRIMARY KEY,
    empresa_id BIGINT NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    
    -- 768-dimensional embedding using paraphrase-multilingual-mpnet-base-v2
    embedding vector(768) NOT NULL,
    
    -- Searchable content for hybrid search
    search_content TEXT NOT NULL,
    razao_social TEXT,
    nome_fantasia TEXT,
    segmento_cliente TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT empresa_embeddings_empresa_id_unique UNIQUE (empresa_id)
);

-- Index for fast lookups by empresa_id
CREATE INDEX IF NOT EXISTS idx_empresa_embeddings_empresa_id 
ON empresa_embeddings(empresa_id);

-- IVFFlat Index for fast approximate nearest neighbor search
-- Note: Requires at least 1M records for optimal performance
-- For smaller datasets, use exact search (no index or HNSW)
-- 
-- For Supabase free tier, use exact search (< 100k records):
CREATE INDEX IF NOT EXISTS idx_empresa_embeddings_embedding 
ON empresa_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Note: For production with > 1M records, consider HNSW index:
-- CREATE INDEX IF NOT EXISTS idx_empresa_embeddings_embedding_hnsw 
-- ON empresa_embeddings USING hnsw (embedding vector_cosine_ops)
-- WITH (m = 16, ef_construction = 64);

-- Comments
COMMENT ON TABLE empresa_embeddings IS 'Vector embeddings for empresa semantic search';
COMMENT ON COLUMN empresa_embeddings.embedding IS '768-dim embedding from paraphrase-multilingual-mpnet-base-v2';
COMMENT ON INDEX idx_empresa_embeddings_embedding IS 'IVFFlat index for cosine similarity search';
