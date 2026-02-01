#!/usr/bin/env python3
"""
GT-28: Import V2 - COMMITS PARCIAIS
Solução para timeout: commit a cada 100 registros
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
engine = create_async_engine(DATABASE_URL, echo=False)

def generate_external_id(chassi: str, data: str) -> str:
    """Gera external_id único"""
    if not chassi or not data:
        import uuid
        return str(uuid.uuid4())
    ext_id = f"{chassi}_{data}"
    return hashlib.md5(ext_id.encode()).hexdigest() if len(ext_id) > 50 else ext_id

def prepare_row(row_dict):
    """Prepara UMA linha"""
    # NaN to None
    for key, value in row_dict.items():
        if pd.isna(value):
            row_dict[key] = None
    
    # Data
    if row_dict.get('data_emplacamento'):
        try:
            from datetime import datetime as dt
            row_dict['data_emplacamento'] = dt.strptime(
                str(row_dict['data_emplacamento']), '%Y-%m-%d'
            ).date()
        except:
            row_dict[key] = None
    
    # Docs
    for col in ['cpf_cnpj_proprietario', 'cod_atividade_economica']:
        if row_dict.get(col):
            try:
                row_dict[col] = str(int(float(row_dict[col])))
            except:
                row_dict[col] = None
    
    # external_id
    row_dict['external_id'] = generate_external_id(
        row_dict.get('chassi'),
        str(row_dict.get('data_emplacamento')) if row_dict.get('data_emplacamento') else None
    )
    
    return row_dict

async def load_with_partial_commits(input_path: str, commit_every: int = 100, test_mode: bool = False):
    """Carga com commits parciais (evita timeout)"""
    print("=" * 60)
    print("💾 GT-28: IMPORT V2 - COMMITS PARCIAIS")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💡 Commit a cada {commit_every} registros")
    print("=" * 60)
    
    # Ler CSV
    print(f"\n📋 Lendo CSV...")
    if test_mode:
        df = pd.read_csv(input_path, sep=';', encoding='utf-8', nrows=10000)
        print(f"🧪 MODO TESTE: {len(df):,} registros")
    else:
        df = pd.read_csv(input_path, sep=';', encoding='utf-8', low_memory=False)
        print(f"📊 Total: {len(df):,} registros")
    
    total_rows = len(df)
    success_count = 0
    error_count = 0
    start_time = datetime.now()
    
    # Processar com commits parciais
    conn = await engine.connect()
    trans = await conn.begin()
    
    with tqdm(total=total_rows, desc="Inserindo") as pbar:
        for idx, row in df.iterrows():
            try:
                row_dict = prepare_row(row.to_dict())
                
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
                
                # Commit parcial a cada X registros
                if (idx + 1) % commit_every == 0:
                    await trans.commit()
                    trans = await conn.begin()
                
            except Exception as e:
                error_count += 1
                if error_count == 1:  # Log apenas primeiro erro
                    print(f"\n⚠️  Erro: {str(e)[:150]}")
            
            pbar.update(1)
            if (idx + 1) % 1000 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = success_count / elapsed if elapsed > 0 else 0
                eta_sec = (total_rows - idx - 1) / rate if rate > 0 else 0
                pbar.set_postfix({
                    'OK': success_count,
                    'Err': error_count,
                    'ETA': f'{int(eta_sec/60)}min',
                    'Rate': f'{int(rate)}/s'
                })
    
    # Commit final
    await trans.commit()
    await conn.close()
    
    duration = (datetime.now() - start_time).total_seconds()
    
    print(f"\n" + "=" * 60)
    print(f"✅ Sucesso: {success_count:,} ({success_count/total_rows*100:.1f}%)")
    print(f"⚠️  Erros: {error_count:,}")
    print(f"⏱️  Tempo: {int(duration/60)}min {int(duration%60)}s")
    print(f"📊 Taxa: {int(success_count/duration)} reg/s")
    print("=" * 60)
    
    return {"success": success_count, "errors": error_count, "duration": duration}

if __name__ == "__main__":
    test_mode = "--full" not in sys.argv
    
    if test_mode:
        print("\n🧪 MODO TESTE: 10.000 registros")
        print("   Use --full para 974k\n")
    
    result = asyncio.run(load_with_partial_commits(
        "data/processed/emplacamentos_normalized.csv",
        commit_every=100,  # Commit a cada 100 linhas
        test_mode=test_mode
    ))
    
    print(f"\n📊 Resultado: {result}")
