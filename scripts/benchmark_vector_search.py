#!/usr/bin/env python3
"""Benchmark similarity search performance."""
import os, time, re
from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer

load_dotenv()

# Load model
model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

# Connect
database_url = os.getenv("DATABASE_URL")
m = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", database_url)
conn = psycopg2.connect(host=m.group(3), port=m.group(4), dbname=m.group(5), user=m.group(1), password=m.group(2))
cur = conn.cursor()

# Test 1: Count embeddings
cur.execute("SELECT COUNT(*) FROM empresa_embeddings")
count = cur.fetchone()[0]
print(f"Embeddings no banco: {count:,}")

# Test 2: Performance benchmark with embedding generation
queries = [
    "transportadora",
    "caminhao",
    "frota",
    "logistica",
    "distribuidora",
]

print("\n=== BENCHMARK SIMILARITY SEARCH ===")
print("(inclui geracao de embedding)")
for query in queries:
    # Generate embedding
    start = time.time()
    emb = model.encode(query)
    emb_str = "[" + ",".join(str(x) for x in emb.tolist()) + "]"
    
    # Search
    cur.execute("SELECT COUNT(*) FROM fleetintel_search_empresas(%s::vector, 5)", (emb_str,))
    cur.fetchone()
    elapsed = (time.time() - start) * 1000
    print(f'  "{query}": {elapsed:.1f}ms')

# Test 3: Show sample results
print("\n=== RESULTADO AMOSTRA: \"transportadora\" ===")
emb = model.encode("transportadora")
emb_str = "[" + ",".join(str(x) for x in emb.tolist()) + "]"
cur.execute("SELECT razao_social, segmento_cliente, similarity FROM fleetintel_search_empresas(%s::vector, 5)", (emb_str,))
for row in cur.fetchall():
    print(f'  [{row[2]:.3f}] {row[0][:50]} | {row[1]}')

cur.close()
conn.close()
print("\n=== TODOS OS TESTES CONCLUIDOS ===")
