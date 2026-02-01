#!/usr/bin/env python3
"""
Script para carregar dados CNAE no banco
"""
import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)


async def load_cnae_data():
    """Carrega dados CNAE no banco"""
    
    print("=" * 60)
    print("📊 CARREGANDO DADOS CNAE")
    print("=" * 60)
    
    # Ler CSV CNAE
    cnae_file = Path("data/raw/CNAE_TRAT.csv")
    print(f"\n📋 Lendo arquivo: {cnae_file}")
    
    df = pd.read_csv(cnae_file)
    print(f"✅ Total de registros: {len(df):,}")
    
    # Mapeamento de colunas CSV → Banco
    df_mapped = df.rename(columns={
        "Seção": "secao",
        "Desc. Seção": "desc_secao",
        "Divisão": "divisao",
        "Desc. Divisão": "desc_divisao",
        "Grupo": "grupo",
        "Desc. Grupo": "desc_grupo",
        "Classe": "classe",
        "Desc. Classe": "desc_classe",
        "Subclasse": "subclasse",
        "Subclasse Tratado": "subclasse_tratado",
        "SalesForce": "salesforce",
        "Denominação": "denominacao",
        "Mercado Endereçável": "mercado_enderecavel",
        "Setor Addiante_v2": "setor_addiante_v2",
        "Atuação": "atuacao",
        "Setor Addiante Agrupado": "setor_addiante_agrupado"
    })
    
    # Converter NaN para None e todos os valores para string
    df_mapped = df_mapped.fillna('')
    df_mapped = df_mapped.astype(str)
    
    # Converter para lista de dicts
    records = df_mapped.to_dict('records')
    
    async with engine.begin() as conn:
        # Verificar se já tem dados
        result = await conn.execute(text("SELECT COUNT(*) FROM cnae_lookup"))
        existing_count = result.scalar()
        
        if existing_count > 0:
            print(f"\n⚠️  Tabela cnae_lookup já tem {existing_count:,} registros")
            print("🗑️  Limpando dados antigos...")
            await conn.execute(text("TRUNCATE TABLE cnae_lookup RESTART IDENTITY CASCADE"))
        
        # Inserir em batch
        print(f"\n📤 Inserindo {len(records):,} registros...")
        
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            
            for record in batch:
                await conn.execute(
                    text("""
                        INSERT INTO cnae_lookup (
                            secao, desc_secao, divisao, desc_divisao, 
                            grupo, desc_grupo, classe, desc_classe, subclasse,
                            subclasse_tratado, salesforce, denominacao, 
                            mercado_enderecavel, setor_addiante_v2, atuacao, 
                            setor_addiante_agrupado
                        ) VALUES (
                            :secao, :desc_secao, :divisao, :desc_divisao,
                            :grupo, :desc_grupo, :classe, :desc_classe, :subclasse,
                            :subclasse_tratado, :salesforce, :denominacao,
                            :mercado_enderecavel, :setor_addiante_v2, :atuacao,
                            :setor_addiante_agrupado
                        )
                    """),
                    record
                )
            
            print(f"   ✅ {min(i+batch_size, len(records)):,}/{len(records):,} registros inseridos")
        
        # Verificar inserção
        result = await conn.execute(text("SELECT COUNT(*) FROM cnae_lookup"))
        final_count = result.scalar()
        
        print(f"\n✅ Total de registros na tabela: {final_count:,}")
    
    print("\n" + "=" * 60)
    print("🎉 DADOS CNAE CARREGADOS COM SUCESSO!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(load_cnae_data())
