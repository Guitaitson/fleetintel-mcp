#!/usr/bin/env python3
"""
GT-28: Import para Supabase
Carrega dados normalizados no banco com UPSERT
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
import time

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+asyncpg://", 1)
engine = create_async_engine(DATABASE_URL, echo=False)

async def upsert_batch(conn, batch_df):
    """UPSERT de um batch"""
    for _, row in batch_df.iterrows():
        row_dict = row.to_dict()
        
        # Converter NaN para None, datas e documentos
        for key, value in row_dict.items():
            if pd.isna(value):
                row_dict[key] = None
            elif key == 'data_emplacamento' and value is not None:
                # Converter string de data para objeto date
                from datetime import datetime as dt
                try:
                    row_dict[key] = dt.strptime(str(value), '%Y-%m-%d').date()
                except:
                    row_dict[key] = None
            elif key in ['cpf_cnpj_proprietario', 'cod_atividade_economica'] and value is not None:
                # Converter números para string (documentos)
                row_dict[key] = str(int(float(value))) if value else None
        
        text("""
            INSERT INTO registrations (
                chassi, placa, marca, modelo, ano_fabricacao, ano_modelo,
                data_emplacamento, cpf_cnpj_proprietario, nome_proprietario,
                cod_atividade_economica, contatos, preco
               ) VAL (
                :chassi, :placa, :marca, :modelo, :ano_fabricacao, :ano_modelo,
                  :da_emplacamento, :cpf_cnpj_proprietario, :nome_proprietario,
                  :c_atividade_economica, CAST(:contatos AS jsonb), :preco
              )
                )
            ON CON CONFLICT (chassi, data_emplacamentoO NFLICT (chassi, data_emplacamento) 
                DO UPDATE SETDATE SET
                    placa = EXCLUDED.plaaa,a = EXCLUDED.placa,
                    nom _ roprie ario =  XCLUDED.nom _ roprieuarpd,
    t_            "dd_ = NOW()
            """),
            row_dict
        )

async def load_to_supabase(input_path: str, batch_size: int = 1000):
    """Carrega dados no Supabase"""
    print("=" * 60)
    print("📤 GT-28: IMPORT SUPABASE")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    df = pd.read_csv(input_path, sep=';', encoding='utf-8')
    total_rows = len(df)
    print(f"\n📋 Total de registros: {total_rows:,}")
    
    async with engine.begin() as conn:
        batches = [df[i:i+batch_size] for i in range(0, total_rows, batch_size)]
        
        for i, batch in enumerate(tqdm(batches, desc="Carregando")):
            try:
                await upsert_batch(conn, batch)
            except Exception as e:
                print(f"\n❌ Erro no batch {i}: {e}")
                continue
    
    print(f"\n✅ {total_rows:,} registros processados!")

if __name__ == "__main__":
    asyncio.run(load_to_supabase("data/processed/emplacamentos_normalized.csv"))
