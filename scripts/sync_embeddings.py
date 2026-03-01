#!/usr/bin/env python3
"""
FleetIntel Embeddings Sync - Versao com Logging e Monitoramento

Este script executa o sync de embeddings com logging em tempo real.
Logsa sao salvos em: logs/embeddings_sync.log
"""

import os
import sys
import argparse
import time
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List

# Setup logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"embeddings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

try:
    from sentence_transformers import SentenceTransformer
    logger.info("sentence-transformers loaded successfully")
except ImportError:
    logger.error("sentence-transformers not installed")
    sys.exit(1)

import psycopg2


# Configuration
BATCH_SIZE = 16  # Reduced for Supabase connection stability
CHECKPOINT_INTERVAL = 5000
MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
MAX_RETRIES = 5
RETRY_DELAY = 10


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


def format_time(seconds):
    """Format seconds to human readable time."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def sync_empresas(full_sync: bool = False):
    """Generate embeddings for empresas with automatic reconnection."""
    logger.info("=" * 60)
    logger.info("FLEETINTEL EMBEDDINGS SYNC - EMPRESAS")
    logger.info("=" * 60)
    logger.info(f"Mode: {'FULL SYNC' if full_sync else 'INCREMENTAL'}")
    logger.info(f"Batch size: {BATCH_SIZE}")
    logger.info(f"Checkpoint interval: {CHECKPOINT_INTERVAL}")
    
    # Load model
    logger.info(f"Loading model: {MODEL_NAME}")
    try:
        model = SentenceTransformer(MODEL_NAME)
        logger.info(f"Model loaded successfully. Dimensions: 768")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return
    
    def get_connection_with_retry(max_retries=MAX_RETRIES):
        """Get database connection with retry logic."""
        for attempt in range(max_retries):
            try:
                conn = get_db_connection()
                conn.autocommit = False
                cur = conn.cursor()
                logger.info(f"Database connection established (attempt {attempt + 1})")
                return conn, cur
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("All connection attempts failed")
                    return None, None
    
    # Initial connection
    conn, cur = get_connection_with_retry()
    if conn is None:
        return
    
    # Fetch empresas
    try:
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
        
        logger.info(f"Total empresas to process: {total:,}")
        
        if total == 0:
            logger.info("All empresas already have embeddings!")
            cur.close()
            conn.close()
            return
        
    except Exception as e:
        logger.error(f"Failed to fetch empresas: {e}")
        cur.close()
        conn.close()
        return
    
    # Calculate estimated time
    estimated_seconds = (total / BATCH_SIZE) * 0.05  # Rough estimate
    logger.info(f"Estimated completion time: ~{format_time(estimated_seconds)}")
    logger.info("Press Ctrl+C to interrupt")
    logger.info("-" * 60)
    
    start_time = datetime.utcnow()
    processed = 0
    successful = 0
    failed = 0
    last_checkpoint = 0
    
    start_total = time.time()
    
    try:
        for i in range(0, total, BATCH_SIZE):
            batch = empresas[i:i+BATCH_SIZE]
            batch_start = time.time()
            
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
            gen_time = time.time() - batch_start
            
            # Insert to database with connection health check
            insert_start = time.time()
            for j, emp in enumerate(batch):
                emb_str = embedding_to_string(embeddings[j].tolist())
                try:
                    # Check connection health before each insert
                    if cur.closed:
                        logger.warning("Cursor closed, reconnecting...")
                        conn, cur = get_connection_with_retry()
                        if conn is None:
                            raise Exception("Failed to reconnect")
                    
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
                    error_str = str(e)[:100]
                    if failed <= 5 or "closed" in error_str.lower():
                        logger.warning(f"Insert error (empresa {emp[0]}): {error_str}")
                    
                    # Try to reconnect on connection errors
                    if "closed" in error_str.lower() or "connection" in error_str.lower():
                        logger.warning("Connection error detected, attempting reconnection...")
                        try:
                            conn.close()
                        except:
                            pass
                        conn, cur = get_connection_with_retry()
                        if conn is None:
                            raise
                
                processed += 1
            
            try:
                conn.commit()
            except Exception as e:
                logger.warning(f"Commit failed: {e}, retrying...")
                conn, cur = get_connection_with_retry()
                if conn is None:
                    raise
                conn.commit()
            
            insert_time = time.time() - insert_start
            batch_total = gen_time + insert_time
            
            # Progress update
            elapsed_total = time.time() - start_total
            rate = processed / elapsed_total if elapsed_total > 0 else 0
            remaining = total - processed
            eta_seconds = remaining / rate if rate > 0 else 0
            
            pct = (processed / total) * 100
            
            # Log every batch
            logger.info(
                f"Progress: {pct:5.1f}% | {processed:,}/{total:,} | "
                f"OK:{successful:,} ERR:{failed:,} | "
                f"Rate: {rate:6.1f}/s | ETA: {format_time(eta_seconds)} | "
                f"Batch: {batch_total:.2f}s"
            )
            
            # Checkpoint
            if processed - last_checkpoint >= CHECKPOINT_INTERVAL:
                last_checkpoint = processed
                elapsed_min = elapsed_total / 60
                logger.info(f"[CHECKPOINT] {processed:,} records | {elapsed_min:.1f}min | {rate:.1f}/s")
    
    except KeyboardInterrupt:
        logger.warning("Interrupted by user!")
        conn.rollback()
    
    # Final stats
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info("FINAL STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Processed: {processed:,}")
    logger.info(f"Successful: {successful:,}")
    logger.info(f"Failed: {failed:,}")
    logger.info(f"Time: {format_time(elapsed)}")
    logger.info(f"Average rate: {successful/elapsed:.1f}/s")
    
    # Verify
    try:
        cur.execute("SELECT COUNT(*) FROM empresa_embeddings")
        count = cur.fetchone()[0]
        logger.info(f"Database total embeddings: {count:,}")
    except Exception as e:
        logger.error(f"Verification query failed: {e}")
    
    cur.close()
    conn.close()
    logger.info("Sync completed!")
    logger.info(f"Log file: {LOG_FILE}")


def main():
    parser = argparse.ArgumentParser(description="Generate empresa embeddings with monitoring")
    parser.add_argument("--mode", default="empresas")
    parser.add_argument("--full", action="store_true", help="Full sync (reprocess all)")
    args = parser.parse_args()
    
    logger.info("Starting FleetIntel Embeddings Sync")
    sync_empresas(full_sync=args.full)


if __name__ == "__main__":
    main()
