#!/usr/bin/env python3
"""
Teste do ETL com 1 REGISTRO APENAS para debug
"""
import asyncio
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://", 1)
engine = create_async_engine(DATABASE_URL, echo=False)

async def test_one_record():
    print("=" * 60)
    print("🧪 TESTE COM 1 REGISTRO")
    print("=" * 60)
    
    # Ler 1 registro
    df = pd.read_csv("data/processed/emplacamentos_normalized.csv", sep=';', encoding='utf-8', nrows=1)
    
    print("\n📋 Dados do registro:")
    row = df.iloc[0]
    print(f"   chassi: '{row['chassi']}'")
    print(f"   cpf_cnpj (original): {row['cpf_cnpj_proprietario']} (tipo: {type(row['cpf_cnpj_proprietario'])})")
    print(f"   marca: '{row['marca']}'")
    print(f"   modelo: '{row['modelo']}'")
    print(f"   data_emplacamento: '{row['data_emplacamento']}'")
    
    # Problema 1: CNPJ como float
    cnpj_float = row['cpf_cnpj_proprietario']
    cnpj_str = str(cnpj_float)
    print(f"\n❌ CNPJ como string direta: '{cnpj_str}'")
    
    # Solução: remover .0 e converter para int primeiro
    if pd.notna(cnpj_float):
        cnpj_int = int(cnpj_float)
        cnpj_fixed = str(cnpj_int)
        print(f"✅ CNPJ corrigido: '{cnpj_fixed}' (len: {len(cnpj_fixed)})")
    
    async with engine.begin() as conn:
        # Testar fix_documento
        result = await conn.execute(
            text("SELECT fix_documento(:doc, 14)"),
            {"doc": cnpj_fixed}
        )
        cnpj_final = result.scalar()
        print(f"✅ CNPJ após fix_documento: '{cnpj_final}' (len: {len(cnpj_final) if cnpj_final else 0})")
        
        # Inserir marca
        await conn.execute(
            text("INSERT INTO marcas (nome) VALUES (:nome) ON CONFLICT (nome) DO NOTHING"),
            {"nome": row['marca']}
        )
        
        result = await conn.execute(
            text("SELECT id FROM marcas WHERE nome = :nome"),
            {"nome": row['marca']}
        )
        marca_id = result.scalar()
        print(f"\n✅ Marca inserida - ID: {marca_id}")
        
        # Inserir modelo
        await conn.execute(
            text("""
                INSERT INTO modelos (marca_id, nome)
                VALUES (:marca_id, :nome)
                ON CONFLICT (marca_id, nome) DO NOTHING
            """),
            {"marca_id": marca_id, "nome": row['modelo']}
        )
        
        result = await conn.execute(
            text("SELECT id FROM modelos WHERE marca_id = :marca_id AND nome = :nome"),
            {"marca_id": marca_id, "nome": row['modelo']}
        )
        modelo_id = result.scalar()
        print(f"✅ Modelo inserido - ID: {modelo_id}")
        
        # Inserir vehicle
        result = await conn.execute(
            text("""
                INSERT INTO vehicles (chassi, marca_id, modelo_id, marca_nome, modelo_nome)
                VALUES (:chassi, :marca_id, :modelo_id, :marca_nome, :modelo_nome)
                ON CONFLICT (chassi) DO UPDATE SET updated_at = NOW()
                RETURNING id
            """),
            {
                "chassi": row['chassi'],
                "marca_id": marca_id,
                "modelo_id": modelo_id,
                "marca_nome": row['marca'],
                "modelo_nome": row['modelo']
            }
        )
        vehicle_id = result.scalar()
        print(f"✅ Vehicle inserido - ID: {vehicle_id}")
        
        # Inserir empresa
        result = await conn.execute(
            text("""
                INSERT INTO empresas (cnpj, razao_social, source)
                VALUES (:cnpj, :razao_social, 'excel')
                ON CONFLICT (cnpj) DO UPDATE SET updated_at = NOW()
                RETURNING id
            """),
            {
                "cnpj": cnpj_final,
                "razao_social": row.get('nome_proprietario')
            }
        )
        empresa_id = result.scalar()
        print(f"✅ Empresa inserida - ID: {empresa_id}")
        
        # Parsear data
        data_emplac = pd.to_datetime(row['data_emplacamento']).date()
        print(f"\n✅ Data parseada: {data_emplac}")
        
        # Verificar se temos tudo
        print(f"\n📊 Preparado para inserir registration:")
        print(f"   vehicle_id: {vehicle_id}")
        print(f"   empresa_id: {empresa_id}")
        print(f"   data_emplacamento: {data_emplac}")
        
        # Inserir registration
        import hashlib
        external_id = hashlib.md5(f"{row['chassi']}_{data_emplac}".encode()).hexdigest()
        
        await conn.execute(
            text("""
                INSERT INTO registrations (external_id, vehicle_id, empresa_id, data_emplacamento, fonte)
                VALUES (:external_id, :vehicle_id, :empresa_id, :data_emplacamento, 'teste')
                ON CONFLICT (external_id) DO NOTHING
            """),
            {
                "external_id": external_id,
                "vehicle_id": vehicle_id,
                "empresa_id": empresa_id,
                "data_emplacamento": data_emplac
            }
        )
        
        print(f"✅ Registration inserido!")
        
        # Verificar
        result = await conn.execute(text("SELECT COUNT(*) FROM registrations WHERE fonte = 'teste'"))
        count = result.scalar()
        print(f"\n✅ Total de registrations de teste: {count}")
    
    await engine.dispose()
    
    print("\n" + "=" * 60)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_one_record())
