# Plano de Implementação: pgvector com Supabase

**Data:** 2026-02-06  
**Status:** Planejado  
**Owner:** FleetIntel MCP

---

## 🎯 Objetivo

Implementar similarity search vetorial no FleetIntel usando pgvector com Supabase para:
- Busca semântica de empresas e veículos
- Redução de latência de query: ~500ms → <100ms
- Suportar até 1M de vetores

---

## 📊 Arquitetura Final

```
┌─────────────────────────────────────────────────────────────────┐
│                    FleetIntel MCP                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Empresas  │    │  Veículos   │    │  Query Cache        │  │
│  │   (SQL)     │    │   (SQL)     │    │  (Redis + pgvector) │  │
│  └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘  │
│         │                   │                       │             │
│         └───────────────────┼───────────────────────┘             │
│                             │                                     │
│                    ┌────────▼────────┐                            │
│                    │  Hybrid Search │                            │
│                    │  + Cache Hit   │                            │
│                    └─────────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Configuração de Embeddings

| Parâmetro | Valor |
|-----------|-------|
| Modelo | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` |
| Dimensões | 768 |
| Provedor | Local (gratuito) |
| Batch Size | 32 |
| Target Query | < 500ms (com cache Redis: < 100ms para queries repetidas) |
| Target SQL | < 50ms |

## 📋 Tasks

### Task 1: Migration pgvector para Supabase
**Arquivo:** `supabase/migrations/20260206000001_pgvector_extension.sql`

```sql
-- Criar extensão pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Verificar instalação
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Dimensões: 768 (paraphrase-multilingual-mpnet-base-v2)
-- Suporta modelos sentence-transformers locais
```

### Task 2: Tabela de Embeddings para Empresas
**Arquivo:** `supabase/migrations/20260206000002_empresa_embeddings.sql`

```sql
-- Tabela de embeddings para empresas
CREATE TABLE empresa_embeddings (
    id SERIAL PRIMARY KEY,
    empresa_id INT NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    
    -- Vetor de embedding (768 dimensões - paraphrase-multilingual-mpnet-base-v2)
    embedding vector(768),
    
    -- Texto fonte usado para gerar o embedding
    source_text TEXT,
    
    -- Metadados de geração
    model_name TEXT DEFAULT 'paraphrase-multilingual-mpnet-base-v2',
    embedding_version INT DEFAULT 1,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Status de geração
    status TEXT CHECK (status IN ('pending', 'completed', 'error')),
    error_message TEXT,
    
    UNIQUE(empresa_id)
);

-- Índices
CREATE INDEX idx_empresa_embeddings_embedding 
ON empresa_embeddings USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX idx_empresa_embeddings_empresa 
ON empresa_embeddings(empresa_id);

CREATE INDEX idx_empresa_embeddings_status 
ON empresa_embeddings(status);

-- Comentários
COMMENT ON TABLE empresa_embeddings IS 'Embeddings vetoriais para busca semântica de empresas';
COMMENT ON COLUMN empresa_embeddings.embedding IS 'Vetor de 1536 dimensões gerado por modelo de embedding';
COMMENT ON COLUMN empresa_embeddings.source_text IS 'Texto concatenado: razao_social + nome_fantasia + segmento_cliente';
```

### Task 3: Tabela de Embeddings para Veículos
**Arquivo:** `supabase/migrations/20260206000003_vehicle_embeddings.sql`

```sql
-- Tabela de embeddings para veículos
CREATE TABLE vehicle_embeddings (
    id SERIAL PRIMARY KEY,
    vehicle_id INT NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    
    -- Vetor de embedding
    embedding vector(768),
    
    -- Texto fonte
    source_text TEXT,
    
    -- Metadados
    model_name TEXT DEFAULT 'paraphrase-multilingual-mpnet-base-v2',
    embedding_version INT DEFAULT 1,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Status
    status TEXT CHECK (status IN ('pending', 'completed', 'error')),
    error_message TEXT,
    
    UNIQUE(vehicle_id)
);

-- Índices
CREATE INDEX idx_vehicle_embeddings_embedding 
ON vehicle_embeddings USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX idx_vehicle_embeddings_vehicle 
ON vehicle_embeddings(vehicle_id);

CREATE INDEX idx_vehicle_embeddings_status 
ON vehicle_embeddings(status);

COMMENT ON TABLE vehicle_embeddings IS 'Embeddings vetoriais para busca semântica de veículos';
```

### Task 4: Funções de Similarity Search
**Arquivo:** `supabase/migrations/20260206000004_vector_functions.sql`

```sql
-- Função: Buscar empresas similares por texto
CREATE OR REPLACE FUNCTION search_similar_empresas(
    query_text TEXT,
    limit_n INT DEFAULT 10,
    min_similarity FLOAT DEFAULT 0.5
) RETURNS TABLE (
    empresa_id INT,
    cnpj CHAR(14),
    razao_social TEXT,
    nome_fantasia TEXT,
    segmento_cliente TEXT,
    similarity FLOAT
) AS $$
DECLARE
    query_embedding vector(1536);
BEGIN
    -- Gerar embedding do texto de query (requer OpenAI API ou pg_vectorize)
    -- Nota: Esta função será implementada no lado da aplicação
    RETURN QUERY
    SELECT 
        e.id,
        e.cnpj,
        e.razao_social,
        e.nome_fantasia,
        e.segmento_cliente,
        1 - (ee.embedding <=> query_embedding) AS similarity
    FROM empresa_embeddings ee
    JOIN empresas e ON ee.empresa_id = e.id
    WHERE ee.status = 'completed'
      AND (1 - (ee.embedding <=> query_embedding)) >= min_similarity
    ORDER BY ee.embedding <=> query_embedding
    LIMIT limit_n;
END;
$$ LANGUAGE plpgsql;

-- Função: Buscar veículos similares por texto
CREATE OR REPLACE FUNCTION search_similar_vehicles(
    query_text TEXT,
    limit_n INT DEFAULT 10,
    min_similarity FLOAT DEFAULT 0.5
) RETURNS TABLE (
    vehicle_id INT,
    chassi TEXT,
    placa TEXT,
    marca_nome TEXT,
    modelo_nome TEXT,
    ano_fabricacao INT,
    similarity FLOAT
) AS $$
DECLARE
    query_embedding vector(1536);
BEGIN
    RETURN QUERY
    SELECT 
        v.id,
        v.chassi,
        v.placa,
        v.marca_nome,
        v.modelo_nome,
        v.ano_fabricacao,
        1 - (ve.embedding <=> query_embedding) AS similarity
    FROM vehicle_embeddings ve
    JOIN vehicles v ON ve.vehicle_id = v.id
    WHERE ve.status = 'completed'
      AND (1 - (ve.embedding <=> query_embedding)) >= min_similarity
    ORDER BY ve.embedding <=> query_embedding
    LIMIT limit_n;
END;
$$ LANGUAGE plpgsql;

-- Função: Gerar texto de embedding para empresa
CREATE OR REPLACE FUNCTION generate_empresa_text(
    e empresas
) RETURNS TEXT AS $$
BEGIN
    RETURN CONCAT_WS(
        ' ',
        e.razao_social,
        COALESCE(e.nome_fantasia, ''),
        COALESCE(e.segmento_cliente, ''),
        COALESCE(e.grupo_locadora, '')
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Função: Gerar texto de embedding para veículo
CREATE OR REPLACE FUNCTION generate_vehicle_text(
    v vehicles
) RETURNS TEXT AS $$
BEGIN
    RETURN CONCAT_WS(
        ' ',
        v.marca_nome,
        v.modelo_nome,
        CAST(v.ano_fabricacao AS TEXT),
        COALESCE(v.cor, ''),
        COALESCE(v.categoria, '')
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;
```

### Task 5: Script ETL de Embeddings
**Arquivo:** `scripts/generate_embeddings.py`

```python
#!/usr/bin/env python3
"""
Script ETL para geração de embeddings usando sentence-transformers.

Usage:
    uv run python scripts/generate_embeddings.py --batch-size 32 --limit 1000
    uv run python scripts/generate_embeddings.py --reprocess-errors
    uv run python scripts/generate_embeddings.py --status-only

Dependencies:
    pip install sentence-transformers
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

import asyncpg
from dotenv import load_dotenv
from openai import AsyncOpenAI
from tqdm import tqdm

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
EMBEDDING_BATCH_SIZE = 100  # Limite da OpenAI API
MAX_CONCURRENT_REQUESTS = 10


async def generate_embedding_batch(
    encoder,
    texts: list[str],
    model: str = EMBEDDING_MODEL
) -> list[list[float]]:
    """Gera embeddings para um batch de textos usando sentence-transformers."""
    embeddings = encoder.encode(texts, normalize_embeddings=True)
    return [emb.tolist() for emb in embeddings]


async def generate_embeddings_for_empresas(
    conn: asyncpg.Connection,
    client: AsyncOpenAI,
    batch_size: int = EMBEDDING_BATCH_SIZE,
    limit: Optional[int] = None,
    reprocess_errors: bool = False
) -> dict:
    """Gera embeddings para empresas pendentes."""
    
    # Query para buscar empresas pendentes
    if reprocess_errors:
        query = """
            SELECT e.id, 
                   CONCAT_WS(' ', e.razao_social, 
                            COALESCE(e.nome_fantasia, ''),
                            COALESCE(e.segmento_cliente, ''),
                            COALESCE(e.grupo_locadora, '')) as source_text
            FROM empresas e
            LEFT JOIN empresa_embeddings ee ON e.id = ee.empresa_id
            WHERE ee.status IN ('error', 'pending') OR ee.id IS NULL
            ORDER BY e.id
        """
    else:
        query = """
            SELECT e.id, 
                   CONCAT_WS(' ', e.razao_social, 
                            COALESCE(e.nome_fantasia, ''),
                            COALESCE(e.segmento_cliente, ''),
                            COALESCE(e.grupo_locadora, '')) as source_text
            FROM empresas e
            LEFT JOIN empresa_embeddings ee ON e.id = ee.empresa_id
            WHERE ee.id IS NULL
            ORDER BY e.id
        """
    
    if limit:
        query += f" LIMIT {limit}"
    
    empresas = await conn.fetch(query)
    
    if not empresas:
        return {"processed": 0, "errors": 0}
    
    total = len(empresas)
    processed = 0
    errors = 0
    
    # Processar em batches
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    async def process_batch(start_idx: int):
        nonlocal processed, errors
        end_idx = min(start_idx + batch_size, total)
        batch = empresas[start_idx:end_idx]
        
        texts = [e["source_text"] for e in batch]
        empresa_ids = [e["id"] for e in batch]
        
        try:
            embeddings = await generate_embedding_batch(client, texts)
            
            # Upsert para o banco
            for emp_id, embedding in zip(empresa_ids, embeddings):
                await conn.execute("""
                    INSERT INTO empresa_embeddings (empresa_id, embedding, source_text, status, generated_at)
                    VALUES ($1, $2, $3, 'completed', NOW())
                    ON CONFLICT (empresa_id) 
                    DO UPDATE SET embedding = $2, source_text = $3, status = 'completed', generated_at = NOW()
                """, emp_id, embedding, texts[empresa_ids.index(emp_id)])
            
            processed += len(batch)
            
        except Exception as e:
            errors += len(batch)
            # Marcar como erro
            for emp_id in empresa_ids:
                await conn.execute("""
                    INSERT INTO empresa_embeddings (empresa_id, embedding, source_text, status, error_message, generated_at)
                    VALUES ($1, $2, $3, 'error', $4, NOW())
                    ON CONFLICT (empresa_id) 
                    DO UPDATE SET status = 'error', error_message = $4, generated_at = NOW()
                """, emp_id, None, texts[empresa_ids.index(emp_id)], str(e))
    
    # Executar batches sequencialmente para evitar rate limiting
    for i in range(0, total, batch_size):
        await process_batch(i)
        await asyncio.sleep(0.1)  # Rate limiting
    
    return {"processed": processed, "errors": errors}


async def generate_embeddings_for_vehicles(
    conn: asyncpg.Connection,
    client: AsyncOpenAI,
    batch_size: int = EMBEDDING_BATCH_SIZE,
    limit: Optional[int] = None,
    reprocess_errors: bool = False
) -> dict:
    """Gera embeddings para veículos pendentes."""
    
    if reprocess_errors:
        query = """
            SELECT v.id, 
                   CONCAT_WS(' ', v.marca_nome, v.modelo_nome,
                            CAST(v.ano_fabricacao AS TEXT),
                            COALESCE(v.cor, '')) as source_text
            FROM vehicles v
            LEFT JOIN vehicle_embeddings ve ON v.id = ve.vehicle_id
            WHERE ve.status IN ('error', 'pending') OR ve.id IS NULL
            ORDER BY v.id
        """
    else:
        query = """
            SELECT v.id, 
                   CONCAT_WS(' ', v.marca_nome, v.modelo_nome,
                            CAST(v.ano_fabricacao AS TEXT),
                            COALESCE(v.cor, '')) as source_text
            FROM vehicles v
            LEFT JOIN vehicle_embeddings ve ON v.id = ve.vehicle_id
            WHERE ve.id IS NULL
            ORDER BY v.id
        """
    
    if limit:
        query += f" LIMIT {limit}"
    
    vehicles = await conn.fetch(query)
    
    if not vehicles:
        return {"processed": 0, "errors": 0}
    
    total = len(vehicles)
    processed = 0
    errors = 0
    
    for i in range(0, total, batch_size):
        batch = vehicles[i:i + batch_size]
        texts = [v["source_text"] for v in batch]
        vehicle_ids = [v["id"] for v in batch]
        
        try:
            embeddings = await generate_embedding_batch(client, texts)
            
            for vid, embedding in zip(vehicle_ids, embeddings):
                await conn.execute("""
                    INSERT INTO vehicle_embeddings (vehicle_id, embedding, source_text, status, generated_at)
                    VALUES ($1, $2, $3, 'completed', NOW())
                    ON CONFLICT (vehicle_id) 
                    DO UPDATE SET embedding = $2, source_text = $3, status = 'completed', generated_at = NOW()
                """, vid, embedding, texts[vehicle_ids.index(vid)])
            
            processed += len(batch)
            
        except Exception as e:
            errors += len(batch)
            for vid in vehicle_ids:
                await conn.execute("""
                    INSERT INTO vehicle_embeddings (vehicle_id, status, error_message, generated_at)
                    VALUES ($1, 'error', $2, NOW())
                    ON CONFLICT (vehicle_id) 
                    DO UPDATE SET status = 'error', error_message = $2, generated_at = NOW()
                """, vid, str(e))
        
        await asyncio.sleep(0.1)
    
    return {"processed": processed, "errors": errors}


async def get_status(conn: asyncpg.Connection) -> dict:
    """Retorna status dos embeddings."""
    empresa_status = await conn.fetchrow("""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'completed') as completed,
            COUNT(*) FILTER (WHERE status = 'pending') as pending,
            COUNT(*) FILTER (WHERE status = 'error') as errors
        FROM empresa_embeddings
    """)
    
    vehicle_status = await conn.fetchrow("""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'completed') as completed,
            COUNT(*) FILTER (WHERE status = 'pending') as pending,
            COUNT(*) FILTER (WHERE status = 'error') as errors
        FROM vehicle_embeddings
    """)
    
    empresa_count = await conn.fetchval("SELECT COUNT(*) FROM empresas")
    vehicle_count = await conn.fetchval("SELECT COUNT(*) FROM vehicles")
    
    return {
        "empresas": {
            "total": empresa_status["total"],
            "total_in_db": empresa_count,
            "completed": empresa_status["completed"],
            "pending": empresa_status["pending"],
            "errors": empresa_status["errors"],
            "progress": f"{empresa_status['completed']/empresa_count*100:.1f}%" if empresa_count > 0 else "0%"
        },
        "vehicles": {
            "total": vehicle_status["total"],
            "total_in_db": vehicle_count,
            "completed": vehicle_status["completed"],
            "pending": vehicle_status["pending"],
            "errors": vehicle_status["errors"],
            "progress": f"{vehicle_status['completed']/vehicle_count*100:.1f}%" if vehicle_count > 0 else "0%"
        }
    }


async def main():
    parser = argparse.ArgumentParser(description="Generate embeddings for FleetIntel data")
    parser.add_argument("--batch-size", type=int, default=EMBEDDING_BATCH_SIZE)
    parser.add_argument("--limit", type=int, default=None, help="Limit records to process")
    parser.add_argument("--reprocess-errors", action="store_true")
    parser.add_argument("--status-only", action="store_true")
    parser.add_argument("--empresas-only", action="store_true")
    parser.add_argument("--vehicles-only", action="store_true")
    args = parser.parse_args()
    
    # Conexão com banco
    conn = await asyncpg.connect(
        host=os.getenv("SUPABASE_HOST"),
        port=os.getenv("SUPABASE_PORT", "5432"),
        user=os.getenv("SUPABASE_USER"),
        password=os.getenv("SUPABASE_PASSWORD"),
        database=os.getenv("SUPABASE_DB")
    )
    
    # Carregar modelo sentence-transformers
    from sentence_transformers import SentenceTransformer
    encoder = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
    
    try:
        if args.status_only:
            status = await get_status(conn)
            print(json.dumps(status, indent=2))
            return
        
        results = {}
        
        if not args.vehicles_only:
            print("Processing empresas...")
            results["empresas"] = await generate_embeddings_for_empresas(
                conn, client, args.batch_size, args.limit, args.reprocess_errors
            )
            print(f"  Processed: {results['empresas']['processed']}, Errors: {results['empresas']['errors']}")
        
        if not args.empresas_only:
            print("Processing vehicles...")
            results["vehicles"] = await generate_embeddings_for_vehicles(
                conn, client, args.batch_size, args.limit, args.reprocess_errors
            )
            print(f"  Processed: {results['vehicles']['processed']}, Errors: {results['vehicles']['errors']}")
        
        print("\nFinal Status:")
        final_status = await get_status(conn)
        print(json.dumps(final_status, indent=2))
        
    finally:
        await conn.close()
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
```

### Task 6: Ferramenta MCP Vector Search
**Arquivo:** `mcp_server/vector_search.py`

```python
"""Vector Search Tools for MCP Server"""

import asyncio
from typing import Optional
from sqlalchemy import text
from openai import AsyncOpenAI

from mcp.server import Server
from mcp.types import Tool, TextContent

from src.fleet_intel_mcp.db.connection import AsyncSessionLocal
from src.fleet_intel_mcp.config import settings


# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_embedding(text: str) -> list[float]:
    """Gera embedding para um texto usando OpenAI."""
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        dimensions=1536
    )
    return response.data[0].embedding


async def search_empresas_similar(
    query: str,
    limit: int = 10,
    min_similarity: float = 0.5
) -> list[dict]:
    """Busca empresas similares usando similarity search vetorial."""
    
    # Gerar embedding da query
    query_embedding = await generate_embedding(query)
    
    async with AsyncSessionLocal() as session:
        # Query de similaridade
        result = await session.execute(text("""
            SELECT 
                e.id,
                e.cnpj,
                e.razao_social,
                e.nome_fantasia,
                e.segmento_cliente,
                e.grupo_locadora,
                1 - (ee.embedding <=> :embedding) AS similarity
            FROM empresa_embeddings ee
            JOIN empresas e ON ee.empresa_id = e.id
            WHERE ee.status = 'completed'
              AND (1 - (ee.embedding <=> :embedding)) >= :min_similarity
            ORDER BY ee.embedding <=> :embedding
            LIMIT :limit
        """), {
            "embedding": query_embedding,
            "min_similarity": min_similarity,
            "limit": limit
        })
        
        rows = result.fetchall()
        return [
            {
                "id": row.id,
                "cnpj": row.cnpj,
                "razao_social": row.razao_social,
                "nome_fantasia": row.nome_fantasia,
                "segmento_cliente": row.segmento_cliente,
                "grupo_locadora": row.grupo_locadora,
                "similarity": float(row.similarity),
            }
            for row in rows
        ]


async def search_vehicles_similar(
    query: str,
    limit: int = 10,
    min_similarity: float = 0.5
) -> list[dict]:
    """Busca veículos similares usando similarity search vetorial."""
    
    query_embedding = await generate_embedding(query)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT 
                v.id,
                v.chassi,
                v.placa,
                v.marca_nome,
                v.modelo_nome,
                v.ano_fabricacao,
                v.ano_modelo,
                v.cor,
                v.categoria,
                1 - (ve.embedding <=> :embedding) AS similarity
            FROM vehicle_embeddings ve
            JOIN vehicles v ON ve.vehicle_id = v.id
            WHERE ve.status = 'completed'
              AND (1 - (ve.embedding <=> :embedding)) >= :min_similarity
            ORDER BY ve.embedding <=> :embedding
            LIMIT :limit
        """), {
            "embedding": query_embedding,
            "min_similarity": min_similarity,
            "limit": limit
        })
        
        rows = result.fetchall()
        return [
            {
                "id": row.id,
                "chassi": row.chassi,
                "placa": row.placa,
                "marca": row.marca_nome,
                "modelo": row.modelo_nome,
                "ano_fabricacao": row.ano_fabricacao,
                "ano_modelo": row.ano_modelo,
                "cor": row.cor,
                "categoria": row.categoria,
                "similarity": float(row.similarity),
            }
            for row in rows
        ]


# MCP Tool Definitions
def register_vector_search_tools(app: Server):
    """Register vector search tools with MCP server."""
    
    @app.list_tools()
    async def list_tools():
        return [
            Tool(
                name="search_empresas_similar",
                description="""
                Busca empresas similares usando similarity search vetorial.
                
                Útil para:
                - Encontrar empresas com perfis semelhantes
                - Busca semântica por segmento/ramo
                - Identificar concorrentes por perfil de frota
                
                Returns empresas ordenadas por similaridade (0-1).
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Texto de busca (ex: 'locadora de veículos', 'empresa de logística')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Número máximo de resultados",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "min_similarity": {
                            "type": "number",
                            "description": "Similaridade mínima (0-1)",
                            "default": 0.5,
                            "minimum": 0,
                            "maximum": 1
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="search_vehicles_similar",
                description="""
                Busca veículos similares usando similarity search vetorial.
                
                Útil para:
                - Encontrar veículos com características similares
                - Busca semântica por tipo/categoria
                - Identificar padrões de frota
                
                Returns veículos ordenados por similaridade (0-1).
                """,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Texto de busca (ex: 'SUV automático', 'caminhão toco')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Número máximo de resultados",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        },
                        "min_similarity": {
                            "type": "number",
                            "description": "Similaridade mínima (0-1)",
                            "default": 0.5,
                            "minimum": 0,
                            "maximum": 1
                        }
                    },
                    "required": ["query"]
                }
            ),
        ]
    
    @app.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "search_empresas_similar":
            results = await search_empresas_similar(
                query=arguments["query"],
                limit=arguments.get("limit", 10),
                min_similarity=arguments.get("min_similarity", 0.5)
            )
            return [TextContent(type="text", text=json.dumps(results))]
        
        elif name == "search_vehicles_similar":
            results = await search_vehicles_similar(
                query=arguments["query"],
                limit=arguments.get("limit", 10),
                min_similarity=arguments.get("min_similarity", 0.5)
            )
            return [TextContent(type="text", text=json.dumps(results))]
        
        raise ValueError(f"Unknown tool: {name}")
```

### Task 7: Atualizar main.py do MCP Server
**Arquivo:** `mcp_server/main.py` (modificar)

```python
# Adicionar imports
from mcp_server.vector_search import register_vector_search_tools

# Registrar tools de vector search
register_vector_search_tools(app)
```

### Task 8: Testes de Performance
**Arquivo:** `scripts/benchmark_vector_search.py`

```python
"""Benchmark script para vector search performance"""

import asyncio
import time
import json
from datetime import datetime

import asyncpg
from openai import AsyncOpenAI

from src.fleet_intel_mcp.config import settings


async def benchmark_vector_search():
    """Executa benchmark de vector search."""
    
    conn = await asyncpg.connect(
        host=settings.SUPABASE_HOST,
        port=settings.SUPABASE_PORT,
        user=settings.SUPABASE_USER,
        password=settings.SUPABASE_PASSWORD,
        database=settings.SUPABASE_DB
    )
    
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Queries de teste
    test_queries = [
        "locadora de veículos",
        "empresa de logística",
        "frota de caminhões",
        "carro automático",
        "SUV familiar",
    ]
    
    results = []
    
    for query in test_queries:
        # Gerar embedding
        start = time.time()
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
            dimensions=1536
        )
        embedding_time = time.time() - start
        embedding = response.data[0].embedding
        
        # Query vector search
        start = time.time()
        result = await conn.fetch("""
            SELECT COUNT(*) as count
            FROM empresa_embeddings ee
            WHERE ee.status = 'completed'
              AND (1 - (ee.embedding <=> $1)) >= 0.5
        """, embedding)
        query_time = time.time() - start
        
        results.append({
            "query": query,
            "embedding_time_ms": embedding_time * 1000,
            "query_time_ms": query_time * 1000,
            "total_time_ms": (embedding_time + query_time) * 1000,
            "matches": result[0]["count"]
        })
        
        print(f"Query: {query}")
        print(f"  Embedding: {embedding_time*1000:.2f}ms")
        print(f"  Search: {query_time*1000:.2f}ms")
        print(f"  Total: {(embedding_time+query_time)*1000:.2f}ms")
        print()
    
    # Resumo
    avg_embedding = sum(r["embedding_time_ms"] for r in results) / len(results)
    avg_query = sum(r["query_time_ms"] for r in results) / len(results)
    avg_total = sum(r["total_time_ms"] for r in results) / len(results)
    
    print("=" * 50)
    print(f"Average Embedding Time: {avg_embedding:.2f}ms")
    print(f"Average Query Time: {avg_query:.2f}ms")
    print(f"Average Total Time: {avg_total:.2f}ms")
    print(f"Target: < 100ms")
    print(f"Status: {'✅ PASSOU' if avg_total < 100 else '❌ FALHOU'}")
    
    await conn.close()
    await client.close()


if __name__ == "__main__":
    asyncio.run(benchmark_vector_search())
```

### Task 9: Documentação de Arquitetura
**Arquivo:** `docs/VECTOR_SEARCH_ARCHITECTURE.md`

```markdown
# Arquitetura de Vector Search - FleetIntel

## Visão Geral

FleetIntel implementa similarity search vetorial usando pgvector com Supabase para permitir busca semântica em empresas e veículos.

## Componentes

### 1. Banco de Dados (Supabase + pgvector)
- **Extensão:** pgvector
- **Tabelas:** `empresa_embeddings`, `vehicle_embeddings`
- **Índices:** IVFFlat para escalabilidade até 1M+ vetores
- **Dimensão:** 1536 (text-embedding-3-small)

### 2. Geração de Embeddings
- **Modelo:** OpenAI text-embedding-3-small
- **API:** AsyncOpenAI para performance
- **Batch Size:** 100 requisições por batch
- **Rate Limiting:** 10 requests concorrentes

### 3. Ferramentas MCP
- `search_empresas_similar`: Busca semântica de empresas
- `search_vehicles_similar`: Busca semântica de veículos
- Parâmetros: query, limit, min_similarity

## Fluxo de Dados

```
1. ETL Load (dados originais)
   ↓
2. Generate Embeddings (script)
   ↓
3. pgvector Storage (tabelas de embeddings)
   ↓
4. Vector Search Query (MCP tools)
   ↓
5. Hybrid Results (SQL + Vector)
```

## Performance

| Métrica | Target | Status |
|---------|--------|--------|
| Embedding Time | < 50ms | Em teste |
| Query Time | < 50ms | Em teste |
| Total Time | < 100ms | Em teste |

## Escalabilidade

- **IVFFlat Index:** Listas = rows / 1000
- **Para 1M registros:** ~1000 listas
- **Updates:** Reindexar apenas partitions afetadas

## Limitações

- Requer chave OpenAI API
- Latência adicional por chamadas API
- Dados sensíveis no texto fonte
```

---

## ✅ Checklist de Validação

- [ ] Extensão pgvector instalada
- [ ] Tabelas de embeddings criadas
- [ ] Índices IVFFlat configurados
- [ ] Funções SQL definidas
- [ ] Script ETL testado
- [ ] Ferramentas MCP registradas
- [ ] Benchmark executado (< 100ms)
- [ ] Documentação atualizada

---

## 📦 Entregáveis

| Arquivo | Descrição |
|---------|-----------|
| `supabase/migrations/20260206000001_pgvector_extension.sql` | Migration: Extensão pgvector |
| `supabase/migrations/20260206000002_empresa_embeddings.sql` | Migration: Tabela empresa_embeddings |
| `supabase/migrations/20260206000003_vehicle_embeddings.sql` | Migration: Tabela vehicle_embeddings |
| `supabase/migrations/20260206000004_vector_functions.sql` | Migration: Funções SQL |
| `scripts/generate_embeddings.py` | Script ETL de embeddings |
| `mcp_server/vector_search.py` | Ferramentas MCP de vector search |
| `scripts/benchmark_vector_search.py` | Script de benchmark |
| `docs/VECTOR_SEARCH_ARCHITECTURE.md` | Documentação de arquitetura |
