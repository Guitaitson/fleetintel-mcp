#!/usr/bin/env python3
"""
GT-28: Import OTIMIZADO - BULK INSERT
Carrega 974k registros em ~30-60 minutos (vs 40 horas)
"""
import asyncio
import pandas as pd
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from tqdm import tqdm
import hashlib

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+asyncpg://", 1)
engine = create_async_engine(DATABASE_URL, echo=False, pool_size=20, max_overflow=0)

def generate_external_id(chassi: str, data: str) -> str:
    """Gera external_id único"""
    if not chassi or not data:
        import uuid
        return str(uuid.uuid4())
    ext_id = f"{chassi}_{data}"
    return hashlib.md5(ext_id.encode()).hexdigest() if len(ext_id) > 50 else ext_id

def prepare_batch_data(batch_df):
    """Prepara TODOS os dados do batch de UMA VEZ (mais rápido)"""
    # 1. Substituir NaN por None em TODAS as colunas de uma vez
    batch_df = batch_df.where(pd.notna(batch_df), None)
    
    # 2. Converter datas (vetorizado)
    if 'data_emplacamento' in batch_df.columns:
        batch_df['data_emplacamento'] = pd.to_datetime(
            batch_df['data_emplacamento'], 
            errors='coerce'
        ).dt.date
    
    # 3. Converter documentos (vetorizado)
    for col in ['cpf_cnpj_proprietario', 'cod_atividade_economica']:
        if col in batch_df.columns:
            batch_df[col] = batch_df[col].apply(
                lambda x: str(int(float(x))) if pd.notna(x) else None
            )
    
    # 4. Gerar external_ids (vetorizado)
    batch_df['external_id'] = batch_df.apply(
        lambda row: generate_external_id(
            row.get('chassi'),
            str(row.get('data_emplacamento')) if row.get('data_emplacamento') else None
        ),
        axis=1
    )
    
    return batch_df

async def bulk_insert_batch(conn, batch_df, batch_num):
    """INSERT em massa usando VALUES múltiplos"""
    try:
        # Preparar dados
        batch_df = prepare_batch_data(batch_df)
        
        # Construir lista de valores
        values_list = []
        for _, row in batch_df.iterrows():
            values_list.append({
                'external_id': row.get('external_id'),
                'chassi': row.get('chassi'),
                'placa': row.get('placa'),
                'marca': row.get('marca'),
                'modelo': row.get('modelo'),
                'ano_fabricacao': row.get('ano_fabricacao'),
                'ano_modelo': row.get('ano_modelo'),
                'data_emplacamento': row.get('data_emplacamento'),
                'cpf_cnpj_proprietario': row.get('cpf_cnpj_proprietario'),
                'nome_proprietario': row.get('nome_proprietario'),
                'cod_atividade_economica': row.get('cod_atividade_economica'),
                'contatos': row.get('contatos'),
                'preco': row.get('preco')
            })
        
        # EXECUTEMANY - muito mais rápido!
        await conn.execute(
            text("""
                INSERT INTO registrations (
                    external_id, chassi, placa, marca, modelo,
                    ano_fabricacao, ano_modelo, data_emplacamento,
                    cpf_cnpj_proprietario, nome_proprietario,
                    cod_atividade_economica, contatos, preco
                ) VALUES (
                    :external_id, :chassi, :placa, :marca, :modelo,
                    :ano_fabricacao, :ano_modelo, :data_emplacamento,
                    :cpf_cnpj_proprietario, :nome_proprietario,
                    :cod_atividade_economica, CAST(:contatos AS jsonb), :preco
                )
                ON CONFLICT (external_id) DO NOTHING
            """),
            values_list  # Lista de dicts - executemany!
        )
        
        return len(batch_df), 0
        
    except Exception as e:
        print(f"\n⚠️  Batch {batch_num} erro: {str(e)[:150]}")
        return 0, len(batch_df)

async def load_to_supabase_optimized(input_path: str, batch_size: int = 5000, test_mode: bool = False):
    """Carga OTIMIZADA com BULK INSERT"""
    print("=" * 60)
    print("🚀 GT-28: IMPORT OTIMIZADO - BULK INSERT")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Ler CSV com chunks para economia de memória
    print(f"\n📋 Lendo CSV...")
    if test_mode:
        df = pd.read_csv(input_path, sep=';', encoding='utf-8', nrows=10000)
        print(f"🧪 MODO TESTE: {len(df):,} registros")
    else:
        df = pd.read_csv(input_path, sep=';', encoding='utf-8', low_memory=False)
        print(f"📊 Total: {len(df):,} registros")
    
    total_rows = len(df)
    total_success = 0
    total_errors = 0
    start_time = datetime.now()
    
    async with engine.begin() as conn:
        batches = [df[i:i+batch_size] for i in range(0, total_rows, batch_size)]
        
        print(f"📦 Processando {len(batches)} batches de {batch_size:,} registros...")
        
        with tqdm(total=len(batches), desc="Batches") as pbar:
            for i, batch in enumerate(batches):
                success, errors = await bulk_insert_batch(conn, batch, i)
                total_success += success
                total_errors += errors
                
                # Calcular tempo estimado
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                eta_seconds = (len(batches) - i - 1) / rate if rate > 0 else 0
                eta_min = int(eta_seconds / 60)
                
                pbar.update(1)
                pbar.set_postfix({
                    'OK': total_success,
                    'Err': total_errors,
                    'ETA': f'{eta_min}min'
                })
    
    duration = (datetime.now() - start_time).total_seconds()
    
    print(f"\n" + "=" * 60)
    print(f"✅ Sucesso: {total_success:,} ({total_success/total_rows*100:.1f}%)")
    print(f"⚠️  Erros: {total_errors:,}")
    print(f"⏱️  Tempo: {int(duration/60)}min {int(duration%60)}s")
    print(f"📊 Taxa: {int(total_success/duration)} registros/segundo")
    print("=" * 60)
    
    return {"success": total_success, "errors": total_errors, "duration": duration}

if __name__ == "__main__":
    test_mode = "--full" not in sys.argv
    
    if test_mode:
        print("\n🧪 MODO TESTE: 10.000 registros")
        print("   Use --full para carga completa (974k)\n")
    
    result = asyncio.run(load_to_supabase_optimized(
        "data/processed/emplacamentos_normalized.csv",
        batch_size=1000,  # 1000 = sweet spot (sem timeout)
        test_mode=test_mode
    ))
    
    print(f"\n📊 Resultado: {result}")
