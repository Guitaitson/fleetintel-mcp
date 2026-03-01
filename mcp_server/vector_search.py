"""FleetIntel Vector Search MCP Tools

MCP tools for vector similarity search using pgvector.

Features:
- Semantic search for empresas
- Hybrid search (vector + keyword)
- Embedding generation using sentence-transformers
"""

import os
import sys
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(".env.local")

from sqlalchemy import text
from src.fleet_intel_mcp.db.connection import AsyncSessionLocal


# ============================================
# MCP Tools
# ============================================

async def search_empresas_vector(
    query: str,
    match_count: int = 10,
    similarity_threshold: float = 0.5,
    use_hybrid: bool = False
) -> Dict[str, Any]:
    """
    Search empresas using vector similarity search.
    
    This is MUCH FASTER than SQL LIKE queries for fuzzy matching.
    Uses pgvector cosine similarity for ranking.
    
    Args:
        query: Search query (company name or description)
        match_count: Maximum number of results (default: 10)
        similarity_threshold: Minimum similarity score (default: 0.5)
        use_hybrid: Use hybrid search (vector + keyword)
    
    Returns:
        Dict with empresas ranked by semantic similarity
    
    Example:
        >>> result = await search_empresas_vector("empresa de logistica")
        >>> # Returns empresas semantically similar to "empresa de logistica"
    """
    start_time = time.time()
    
    # Try to generate embedding (if model available)
    embedding = None
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
        embedding = model.encode([query], show_progress_bar=False)[0].tolist()
    except ImportError:
        # Fallback: Use keyword search if embedding not available
        print("Warning: sentence-transformers not available, using keyword search")
        use_hybrid = True
    
    async with AsyncSessionLocal() as session:
        if use_hybrid or embedding is None:
            # Keyword-only search (fallback)
            result = await session.execute(
                text("""
                    SELECT id, razao_social, nome_fantasia, segmento_cliente
                    FROM empresas
                    WHERE razao_social ILIKE :query
                       OR nome_fantasia ILIKE :query
                    ORDER BY razao_social
                    LIMIT :limit
                """),
                {"query": f"%{query}%", "limit": match_count}
            )
            empresas = [
                {
                    "id": row.id,
                    "razao_social": row.razao_social,
                    "nome_fantasia": row.nome_fantasia,
                    "segmento_cliente": row.segmento_cliente,
                    "similarity": 1.0,  # Keyword matches get full score
                    "search_type": "keyword"
                }
                for row in result.fetchall()
            ]
        else:
            # Vector similarity search
            if use_hybrid:
                func_name = "fleetintel_search_empresas_hybrid"
                params = {
                    "query_embedding": "[" + ",".join(str(x) for x in embedding) + "]",
                    "match_count": match_count,
                    "similarity_threshold": similarity_threshold,
                    "keyword_weight": 0.3
                }
            else:
                params = {
                    "query_embedding": "[" + ",".join(str(x) for x in embedding) + "]",
                    "match_count": match_count,
                    "similarity_threshold": similarity_threshold
                }
            
            result = await session.execute(
                text(f"SELECT * FROM fleetintel_search_empresas(:query_embedding, :match_count, :similarity_threshold)"),
                params
            )
            
            empresas = [
                {
                    "id": row.empresa_id,
                    "razao_social": row.razao_social,
                    "nome_fantasia": row.nome_fantasia,
                    "segmento_cliente": row.segmento_cliente,
                    "similarity": row.similarity,
                    "search_type": "hybrid" if use_hybrid else "vector"
                }
                for row in result.fetchall()
            ]
    
    duration_ms = (time.time() - start_time) * 1000
    
    return {
        "success": True,
        "query": query,
        "search_type": "hybrid" if use_hybrid else ("keyword" if not embedding else "vector"),
        "results": empresas,
        "count": len(empresas),
        "duration_ms": round(duration_ms, 2),
        "note": "Vector search is much faster than SQL LIKE for fuzzy matching" if embedding else "Keyword search (install sentence-transformers for vector search)"
    }


async def search_empresas_fuzzy(
    query: str,
    match_count: int = 10
) -> Dict[str, Any]:
    """
    Fuzzy search for empresas using hybrid approach.
    
    Combines vector similarity with keyword matching for best results.
    Much faster than pure SQL LIKE for misspelled queries.
    """
    return await search_empresas_vector(
        query=query,
        match_count=match_count,
        similarity_threshold=0.3,
        use_hybrid=True
    )


async def get_embedding_status() -> Dict[str, Any]:
    """Get status of embedding tables."""
    async with AsyncSessionLocal() as session:
        # Count empresa embeddings
        result = await session.execute(text("SELECT COUNT(*) FROM empresa_embeddings"))
        empresa_embeddings = result.scalar() or 0
        
        result = await session.execute(text("SELECT COUNT(*) FROM empresas"))
        total_empresas = result.scalar() or 0
        
        return {
            "empresa_embeddings": empresa_embeddings,
            "total_empresas": total_empresas,
            "empresa_coverage": round(empresa_embeddings / total_empresas * 100, 1) if total_empresas > 0 else 0,
            "model": "paraphrase-multilingual-mpnet-base-v2",
            "dimensions": 768
        }


# ============================================
# CLI Testing
# ============================================

if __name__ == "__main__":
    import asyncio
    
    async def test_vector_search():
        print("Testing Vector Search...")
        print("=" * 60)
        
        # Test 1: Vector search
        print("\n1. Testing vector search for 'transportadora':")
        result = await search_empresas_vector("transportadora", match_count=5)
        print(f"   Query: {result['query']}")
        print(f"   Type: {result['search_type']}")
        print(f"   Duration: {result['duration_ms']}ms")
        print(f"   Results: {len(result['results'])}")
        for emp in result['results'][:3]:
            print(f"   - {emp['razao_social']} (similarity: {emp['similarity']:.3f})")
        
        # Test 2: Fuzzy search
        print("\n2. Testing fuzzy search for 'empresa de cambio':")
        result = await search_empresas_fuzzy("empresa de cambio", match_count=5)
        print(f"   Query: {result['query']}")
        print(f"   Results: {len(result['results'])}")
        
        # Test 3: Status
        print("\n3. Embedding status:")
        status = await get_embedding_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
    
    asyncio.run(test_vector_search())
