#!/usr/bin/env python3
"""
Script de TESTE - Import de 10 registros para validar estrutura
"""
import asyncio
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from datetime import datetime as dt

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+asyncpg://", 1)
engine = create_async_engine(DATABASE_URL, echo=True)  # echo=True para ver SQL

async def test_import():
    print("=" * 60)
    print("🧪 TESTE DE IMPORT - 10 REGISTROS")
    print("=" * 60)
    
    # Ler apenas 10 registros
    df = pd.read_csv("data/processed/emplacamentos_normalized.csv", sep=';', nrows=10)
    print(f"\n📋 Lendo {len(df)} registros para teste")
    print(f"📊 Colunas: {list(df.columns)}")
    
    async with engine.begin() as conn:
        # 1. Verificar se índice UNIQUE existe
        result = await conn.execute(text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'registrations' 
            AND indexdef LIKE '%UNIQUE%'
        """))
        print("\n🔍 Índices UNIQUE na tabela:")
        for row in result:
            print(f"   - {row[0]}: {row[1]}")
        
        # 2. Testar INSERT de 1 registro
        print("\n🧪 Testando INSERT de 1 registro...")
        row = df.iloc[0].to_dict()
        
        # Conversões
        for key, value in row.items():
            if pd.isna(value):
                row[key] = None
            elif key == 'data_emplacamento' and value:
                try:
                    row[key] = dt.strptime(str(value), '%Y-%m-%d').date()
                except:
                    row[key] = None
            elif key in ['cpf_cnpj_proprietario', 'cod_atividade_economica'] and value:
                row[key] = str(int(float(value)))
        
        print(f"\n📝 Dados a inserir:")
        print(f"   chassi: {row.get('chassi')}")
        print(f"   placa: {row.get('placa')}")
        print(f"   data_emplacamento: {row.get('data_emplacamento')}")
        print(f"   contatos: {row.get('contatos')}")
        
        try:
            # Tentar INSERT simples
            await conn.execute(
                text("""
                    INSERT INTO registrations (
                        chassi, placa, marca, modelo, ano_fabricacao, ano_modelo,
                        data_emplacamento, cpf_cnpj_proprietario, nome_proprietario,
                        cod_atividade_economica, contatos, preco
                    ) VALUES (
                        :chassi, :placa, :marca, :modelo, :ano_fabricacao, :ano_modelo,
                        :data_emplacamento, :cpf_cnpj_proprietario, :nome_proprietario,
                        :cod_atividade_economica, CAST(:contatos AS jsonb), :preco
                    )
                """),
                row
            )
            print("✅ INSERT bem-sucedido!")
            
            # Verificar se foi inserido
            result = await conn.execute(text("""
                SELECT COUNT(*) FROM registrations WHERE chassi = :chassi
            """), {"chassi": row['chassi']})
            count = result.scalar()
            print(f"✅ Registro encontrado no banco: {count}")
            
        except Exception as e:
            print(f"❌ ERRO no INSERT: {e}")
            print(f"\nTipo do erro: {type(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(test_import())
