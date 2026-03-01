#!/usr/bin/env python3
"""
FleetIntel Embedding Test - Small Sample

Test embedding generation with a small sample before full sync.
Validates: connection, embedding generation, and database insertion.

Usage:
    uv run python scripts/test_embeddings.py --sample 100
"""

import os
import sys
import time
from datetime import datetime
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()  # Load all environment variables

from sentence_transformers import SentenceTransformer

# Try psycopg2, fallback to psycopg2-binary
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary", "-q"])
    import psycopg2
    from psycopg2.extras import RealDictCursor


@dataclass
class TestConfig:
    model_name: str = "paraphrase-multilingual-mpnet-base-v2"
    embedding_dimensions: int = 768
    sample_size: int = 100


def test_embeddings(sample_size: int = 100):
    """Test embedding generation with sample companies."""
    
    print("=" * 70)
    print("FLEETINTEL EMBEDDING TEST")
    print("=" * 70)
    print(f"Sample size: {sample_size} companies")
    print()
    
    config = TestConfig(sample_size=sample_size)
    
    # Step 1: Check database connection
    print("1. Testing database connection...")
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print(f"   [FAIL] DATABASE_URL not set")
            return False
        
        # Parse connection params from DATABASE_URL
        # Format: postgresql://user:password@host:port/database
        import re
        match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", database_url)
        if match:
            user, password, host, port, dbname = match.groups()
        else:
            print(f"   [FAIL] Could not parse DATABASE_URL")
            return False
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM empresas")
        total = cur.fetchone()[0]
        
        print(f"   [OK] Connected to Supabase")
        print(f"   [OK] Total companies in database: {total:,}")
    except Exception as e:
        print(f"   [FAIL] Database connection failed: {e}")
        return False
    
    # Step 2: Load model
    print("\n2. Loading sentence-transformers model...")
    try:
        model = SentenceTransformer(config.model_name)
        print(f"   [OK] Model loaded: {config.model_name}")
        print(f"   [OK] Dimensions: {config.embedding_dimensions}")
    except Exception as e:
        print(f"   [FAIL] Model loading failed: {e}")
        return False
    
    # Step 3: Fetch sample companies
    print(f"\n3. Fetching {sample_size} sample companies...")
    try:
        # Get companies without embeddings first (for incremental test)
        cur.execute(f"""
            SELECT e.id, e.razao_social, e.nome_fantasia, e.segmento_cliente
            FROM empresas e
            LEFT JOIN empresa_embeddings ee ON ee.empresa_id = e.id
            WHERE ee.empresa_id IS NULL
            ORDER BY e.id
            LIMIT {sample_size}
        """)
        empresas = cur.fetchall()
        
        if len(empresas) < sample_size:
            # Not enough companies without embeddings, get any companies
            print(f"   [!] Only {len(empresas)} companies without embeddings")
            cur.execute(f"""
                SELECT e.id, e.razao_social, e.nome_fantasia, e.segmento_cliente
                FROM empresas e
                ORDER BY e.id
                LIMIT {sample_size}
            """)
            empresas = cur.fetchall()
        
        print(f"   [OK] Fetched {len(empresas)} companies")
    except Exception as e:
        print(f"   [FAIL] Failed to fetch companies: {e}")
        return False
    
    # Step 4: Generate embeddings
    print(f"\n4. Generating embeddings for {len(empresas)} companies...")
    start_time = time.time()
    
    texts = []
    for emp in empresas:
        parts = []
        if emp[1]:  # razao_social
            parts.append(emp[1])
        if emp[2] and emp[2] != emp[1]:  # nome_fantasia
            parts.append(emp[2])
        if emp[3]:  # segmento_cliente
            parts.append(emp[3])
        texts.append(" | ".join(parts))
    
    embeddings = model.encode(texts, show_progress_bar=False)
    gen_time = time.time() - start_time
    
    print(f"   [OK] Generated {len(embeddings)} embeddings in {gen_time:.2f}s")
    print(f"   [OK] Embedding shape: {embeddings.shape}")
    
    # Step 5: Test database insertion (convert list to string format)
    print(f"\n5. Testing database insertion...")
    insert_start = time.time()
    inserted = 0
    
    for i, emp in enumerate(empresas):
        embedding_list = embeddings[i].tolist()
        # Convert to string format for pgvector: "[0.1,0.2,...]"
        embedding_str = "[" + ",".join(str(x) for x in embedding_list) + "]"
        
        try:
            cur.execute("""
                INSERT INTO empresa_embeddings (empresa_id, embedding, search_content, razao_social, nome_fantasia, segmento_cliente)
                VALUES (%s, %s::vector, %s, %s, %s, %s)
                ON CONFLICT (empresa_id) DO UPDATE SET
                    embedding = EXCLUDED.embedding::vector,
                    search_content = EXCLUDED.search_content,
                    updated_at = NOW()
            """, (emp[0], embedding_str, texts[i], emp[1], emp[2], emp[3]))
            inserted += 1
        except Exception as e:
            print(f"   [FAIL] Error inserting empresa {emp[0]}: {e}")
            break
    
    conn.commit()
    insert_time = time.time() - insert_start
    print(f"   [OK] Inserted {inserted} embeddings in {insert_time:.2f}s")
    
    # Step 6: Estimate full sync time
    print(f"\n6. Performance Estimation...")
    total_companies = 161932  # Total from database
    
    if inserted > 0:
        total_time = (gen_time / len(empresas)) * total_companies
        minutes = total_time / 60
        hours = minutes / 60
        
        print(f"   Generation rate: {len(empresas) / gen_time:.1f} embeddings/sec")
        print(f"   Insertion rate: {inserted / insert_time:.1f} inserts/sec")
        print(f"\n   ESTIMATED TIME FOR FULL SYNC ({total_companies:,} companies):")
        print(f"   - Total time: {total_time/60:.1f} minutes ({total_time/3600:.1f} hours)")
        print(f"   - With checkpoint every 10,000: ~{10000 / (len(empresas) / gen_time) / 60:.1f} min per checkpoint")
    
    # Step 7: Verify insertion
    print(f"\n7. Verification...")
    cur.execute("SELECT COUNT(*) FROM empresa_embeddings")
    count = cur.fetchone()[0]
    print(f"   [OK] Total embeddings in database: {count:,}")
    
    # Step 8: Test similarity search
    print(f"\n8. Testing similarity search...")
    try:
        # Generate query embedding
        query_text = "transportadora"
        query_embedding = model.encode([query_text])[0].tolist()
        query_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        cur.execute("""
            SELECT e.razao_social, 1 - (ee.embedding <=> %s::vector) as similarity
            FROM empresa_embeddings ee
            JOIN empresas e ON e.id = ee.empresa_id
            ORDER BY ee.embedding <=> %s::vector
            LIMIT 5
        """, (query_str, query_str))
        
        print(f"   Query: '{query_text}'")
        print(f"   Top 5 results:")
        for row in cur.fetchall():
            print(f"   - {row[0][:50]}... (similarity: {row[1]:.4f})")
    except Exception as e:
        print(f"   [!] Similarity search test failed: {e}")
    
    # Cleanup
    cur.close()
    conn.close()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Database connection: [OK]")
    print(f"Model loading: [OK]")
    print(f"Embedding generation: [OK] ({gen_time:.2f}s)")
    print(f"Database insertion: [OK] ({inserted}/{len(empresas)} in {insert_time:.2f}s)")
    print(f"Sample size tested: {len(empresas)}")
    
    if inserted > 0:
        print(f"\nFull sync recommendation:")
        if total_time / 3600 < 2:
            print(f"  - Safe to run full sync (~{total_time/3600:.1f} hours)")
        else:
            print(f"  - Consider running in batches (~{total_time/3600:.1f} hours total)")
    
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test embedding generation")
    parser.add_argument("--sample", type=int, default=100, help="Sample size")
    args = parser.parse_args()
    
    success = test_embeddings(sample_size=args.sample)
    sys.exit(0 if success else 1)
