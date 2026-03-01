#!/usr/bin/env python3
"""
FleetIntel Embedding Generator ETL - Version with Real-time Progress

Generate vector embeddings for empresas with real-time progress updates.
"""

import os
import sys
import argparse
import time
import re
from datetime import datetime
from typing import List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Warning: sentence-transformers not installed")
    SentenceTransformer = None

import psycopg2


# Configuration
BATCH_SIZE = 32
CHECKPOINT_INTERVAL = 10000
MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"


def get_db_connection():
    """Create database connection from DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", database_url)
    if match:
        user, password, host, port, dbname = match.groups()
        return psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
    raise ValueError("DATABASE_URL not set")


def embedding_to_string(embedding: List[float]) -> str:
    """Convert list to pgvector format: '[0.1,0.2,...]'"""
    return "[" + ",".join(str(x) for x in embedding) + "]"


def sync_empresas(full_sync: bool = False):
    """Generate embeddings for empresas."""
    print("\n" + "="*60)
    print("FLEETINTEL EMBEDDING GENERATOR - EMPRESAS")
    print("="*60)
    print(f"Mode: {'FULL SYNC' if full_sync else 'INCREMENTAL'}")
    
    # Load model
    print("\nLoading model...")
    model = SentenceTransformer(MODEL_NAME)
    print(f"Model: {MODEL_NAME}")
    print(f"Dimensions: 768")
    
    # Connect to database
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch empresas
    if full_sync:
        cur.execute("SELECT id, razao_social, nome_fantasia, segmento_cliente FROM empresas ORDER BY id")
    else:
        cur.execute("""
            SELECT e.id, e.razao_social, e.nome_fantasia, e.segmento_cliente
            FROM empresas e
            WHERE NOT EXISTS (SELECT 1 FROM empresa_embeddings ee WHERE ee.empresa_id = e.id)
            ORDER BY e.id
        """)
    
    empresas = cur.fetchall()
    total = len(empresas)
    
    print(f"Total empresas: {total:,}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Estimated time: ~{total / 90 / 60:.1f} minutes")
    print("="*60)
    print("Starting... Press Ctrl+C to interrupt\n")
    
    if total == 0:
        print("All empresas already have embeddings!")
        cur.close()
        conn.close()
        return
    
    start_time = datetime.utcnow()
    processed = 0
    successful = 0
    failed = 0
    
    try:
        for i in range(0, total, BATCH_SIZE):
            batch = empresas[i:i+BATCH_SIZE]
            
            # Prepare texts
            texts = []
            for emp in batch:
                parts = []
                if emp[1]: parts.append(emp[1])
                if emp[2] and emp[2] != emp[1]: parts.append(emp[2])
                if emp[3]: parts.append(emp[3])
                texts.append(" | ".join(parts))
            
            # Generate embeddings
            embeddings = model.encode(texts, show_progress_bar=False)
            
            # Insert to database
            for j, emp in enumerate(batch):
                emb_str = embedding_to_string(embeddings[j].tolist())
                try:
                    cur.execute("""
                        INSERT INTO empresa_embeddings 
                        (empresa_id, embedding, search_content, razao_social, nome_fantasia, segmento_cliente)
                        VALUES (%s, %s::vector, %s, %s, %s, %s)
                        ON CONFLICT (empresa_id) DO UPDATE SET
                            embedding = EXCLUDED.embedding::vector,
                            search_content = EXCLUDED.search_content
                    """, (emp[0], emb_str, texts[j], emp[1], emp[2], emp[3]))
                    successful += 1
                except Exception as e:
                    failed += 1
                    if failed <= 3:
                        print(f"Error inserting {emp[0]}: {e}")
                
                processed += 1
            
            conn.commit()
            
            # Progress update
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            rate = processed / elapsed if elapsed > 0 else 0
            remaining = total - processed
            eta = remaining / rate if rate > 0 else 0
            
            pct = (processed / total) * 100
            bar_len = 30
            filled = int(bar_len * pct / 100)
            bar = "=" * filled + "-" * (bar_len - filled)
            
            print(f"\r[{bar}] {pct:5.1f}% | {processed:,}/{total:,} | OK:{successful:,} ERR:{failed:,} | {rate:6.1f}/s | ETA:{eta/60:5.1f}m", end="", flush=True)
            
            # Checkpoint
            if processed % CHECKPOINT_INTERVAL < BATCH_SIZE:
                elapsed_min = elapsed / 60
                print(f"\n--- CHECKPOINT {processed:,} | {elapsed_min:.1f}min | {rate:.1f}/s ---")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user!")
        conn.rollback()
    
    # Final stats
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    print(f"\n\n{'='*60}")
    print("FINAL STATISTICS")
    print("="*60)
    print(f"Processed: {processed:,}")
    print(f"Successful: {successful:,}")
    print(f"Failed: {failed:,}")
    print(f"Time: {elapsed/60:.2f} minutes")
    print(f"Rate: {successful/elapsed:.1f}/s")
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM empresa_embeddings")
    count = cur.fetchone()[0]
    print(f"\nDatabase: {count:,} embeddings")
    
    cur.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Generate empresa embeddings")
    parser.add_argument("--mode", default="empresas")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    
    sync_empresas(full_sync=args.full)


if __name__ == "__main__":
    main()
