#!/usr/bin/env python3
"""
GT-28: Import para Supabase - VERSÃO FINAL CORRIGIDA
Carrega dados normalizados no banco com todas as validações necessárias
"""
import asyncio
import pandas as pd
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from tqdm import tqdm
import hashlib

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+asyncpg://", 1)
engine = create_async_engine(DATABASE_URL, echo=False)

def generate_external_id(chassi: str, data_emplacamento: str) -> str:
    """
    Gera external_id único e determinístico
    Formato: chassi_YYYY-MM-DD (ou hash se muito longo)
    """
    if not chassi or not data_emplacamento:
        # Fallback: gerar hash único
        import uuid
        return str(uuid.uuid4())
    
    # Formato: chassi_data
    external_id = f"{chassi}_{data_emplacamento}"
    
    # Se muito longo, usar hash
    if len(external_id) > 50:
        hash_obj = hashlib.md5(external_id.encode())
        external_id = hash_obj.hexdigest()
    
    return external_id

async def upsert_batch(conn, batch_df, batch_num):
    """UPSERT de um batch com tratamento de erros"""
    success_count = 0
    error_count = 0
    
    for idx, row in batch_df.iterrows():
        row_dict = row.to_dict()
        
        # 1. Converter NaN para None
        for key, value in row_dict.items():
            if pd.isna(value):
                row_dict[key] = None
        
        # 2. Converter data_emplacamento para date object
        if row_dict.get('data_emplacamento'):
            try:
                from datetime import datetime as dt
                row_dict['data_emplacamento'] = dt.strptime(
                    str(row_dict['data_emplacamento']), '%Y-%m-%d'
                ).date()
            except:
                row_dict['data_emplacamento'] = None
        
        # 3. Converter documentos (float → string)
        for doc_field in ['cpf_cnpj_proprietario', 'cod_atividade_economica']:
            if row_dict.get(doc_field):
                try:
                    row_dict[doc_field] = str(int(float(row_dict[doc_field])))
                except:
                    row_dict[doc_field] = None
        
        # 4. CRITICAL: Gerar external_id
        row_dict['external_id'] = generate_external_id(
            row_dict.get('chassi'),
            str(row_dict.get('data_emplacamento')) if row_dict.get('data_emplacamento') else None
        )
        
        try:
            # INSERT simples (sem ON CONFLICT por enquanto para evitar problemas)
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
                row_dict
            )
            success_count += 1
            
        except Exception as e:
            error_count += 1
            # Log apenas primeiro erro de cada batch
            if error_count == 1:
                print(f"\n⚠️  Batch {batch_num} - Primeiro erro: {str(e)[:200]}")
    
    return success_count, error_count

async def load_to_supabase(input_path: str, batch_size: int = 1000, test_mode: bool = False):
    """Carrega dados no Supabase"""
    print("=" * 60)
    print("📤 GT-28: IMPORT SUPABASE - FINAL")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Ler CSV
    if test_mode:
        df = pd.read_csv(input_path, sep=';', encoding='utf-8', nrows=100)
        print(f"\n🧪 MODO TESTE: Carregando apenas 100 registros")
    else:
        df = pd.read_csv(input_path, sep=';', encoding='utf-8')
    
    total_rows = len(df)
    print(f"\n📋 Total de registros: {total_rows:,}")
    
    total_success = 0
    total_errors = 0
    
    async with engine.begin() as conn:
        batches = [df[i:i+batch_size] for i in range(0, total_rows, batch_size)]
        
        with tqdm(total=len(batches), desc="Processando batches") as pbar:
            for i, batch in enumerate(batches):
                success, errors = await upsert_batch(conn, batch, i)
                total_success += success
                total_errors += errors
                pbar.update(1)
                pbar.set_postfix({
                    'Sucesso': total_success,
                    'Erros': total_errors
                })
    
    print(f"\n" + "=" * 60)
    print(f"✅ Registros inseridos com sucesso: {total_success:,}")
    print(f"⚠️  Registros com erro/duplicados: {total_errors:,}")
    print(f"📊 Taxa de sucesso: {(total_success/total_rows*100):.2f}%")
    print("=" * 60)
    
    return {"success": total_success, "errors": total_errors, "total": total_rows}

if __name__ == "__main__":
    # Modo teste por padrão (usar --full para carga completa)
    test_mode = "--full" not in sys.argv
    
    if test_mode:
        print("\n🧪 Executando em MODO TESTE (100 registros)")
        print("   Use --full para carga completa\n")
    
    result = asyncio.run(load_to_supabase(
        "data/processed/emplacamentos_normalized.csv",
        batch_size=1000,
        test_mode=test_mode
    ))
    
    print(f"\n📊 Resultado final: {result}")
