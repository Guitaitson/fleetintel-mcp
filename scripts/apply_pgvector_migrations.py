#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply pgvector migrations to Supabase.

Usage:
    uv run python scripts/apply_pgvector_migrations.py
"""
import os
import sys

# Fix Windows console encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(".env.local")

from sqlalchemy import text
from src.fleet_intel_mcp.db.connection import AsyncSessionLocal


def print_status(msg, status="OK"):
    """Print status message with ASCII-safe symbols."""
    symbols = {
        "OK": "[OK]",
        "FAIL": "[FAIL]",
        "SKIP": "[SKIP]",
        "INFO": "[INFO]",
    }
    print(f"   {symbols.get(status, '[--]')} {msg}")


async def check_and_apply_migrations():
    """Check if pgvector is installed and apply migrations."""
    
    print("=" * 70)
    print("FleetIntel pgvector Migration")
    print("=" * 70)
    
    async with AsyncSessionLocal() as session:
        # Check if pgvector exists
        print("\n1. Checking for pgvector extension...")
        result = await session.execute(text(
            "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'"
        ))
        row = result.fetchone()
        
        if row:
            print_status(f"pgvector {row.extversion} is installed", "OK")
        else:
            print_status("pgvector not found", "FAIL")
            print("\n[!] pgvector extension is not installed on Supabase.")
            print("    To enable it, you need to:")
            print("    1. Contact Supabase support to enable pgvector")
            print("    2. OR use a separate vector database (Qdrant, Pinecone)")
            print("\n    For now, we'll create the table schema but vector")
            print("    operations will use keyword search as fallback.")
            return False
        
        # Check empresas table
        print("\n2. Checking empresas table...")
        result = await session.execute(text("SELECT COUNT(*) FROM empresas"))
        count = result.scalar() or 0
        print_status(f"empresas table has {count} records", "OK")
        
        # Create empresa_embeddings table
        print("\n3. Creating empresa_embeddings table...")
        try:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS empresa_embeddings (
                    id BIGSERIAL PRIMARY KEY,
                    empresa_id BIGINT NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
                    embedding vector(768) NOT NULL,
                    search_content TEXT NOT NULL,
                    razao_social TEXT,
                    nome_fantasia TEXT,
                    segmento_cliente TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    CONSTRAINT empresa_embeddings_empresa_id_unique UNIQUE (empresa_id)
                )
            """))
            await session.commit()
            print_status("empresa_embeddings table created", "OK")
        except Exception as e:
            print_status(f"Failed: {e}", "FAIL")
        
        # Create IVFFlat index
        print("\n4. Creating IVFFlat index...")
        try:
            await session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_empresa_embeddings_embedding 
                ON empresa_embeddings USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
            await session.commit()
            print_status("IVFFlat index created", "OK")
        except Exception as e:
            print_status(f"Index creation skipped: {e}", "SKIP")
        
        # Create search functions
        print("\n5. Creating search functions...")
        try:
            await session.execute(text("""
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
            """))
            await session.commit()
            print_status("fleetintel_search_empresas function created", "OK")
        except Exception as e:
            print_status(f"Function creation skipped: {e}", "SKIP")
        
        # Verify setup
        print("\n6. Verification...")
        result = await session.execute(text("SELECT COUNT(*) FROM empresa_embeddings"))
        emb_count = result.scalar() or 0
        
        result = await session.execute(text("""
            SELECT routine_name FROM information_schema.routines 
            WHERE routine_name = 'fleetintel_search_empresas'
        """))
        func_exists = result.fetchone() is not None
        
        print_status(f"empresa_embeddings: {emb_count} records", "INFO")
        print_status(f"fleetintel_search_empresas: {'exists' if func_exists else 'missing'}", 
                     "OK" if func_exists else "FAIL")
        
        print("\n" + "=" * 70)
        print("MIGRATION COMPLETE")
        print("=" * 70)
        
        if emb_count == 0:
            print("\n[!] Next steps:")
            print("    1. Install sentence-transformers: uv add sentence-transformers")
            print("    2. Generate embeddings: uv run python scripts/generate_embeddings.py --full")
            print("    3. Test search: uv run python scripts/benchmark_vector_search.py")
        
        return True


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(check_and_apply_migrations())
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
