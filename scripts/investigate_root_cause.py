#!/usr/bin/env python3
"""
Script para investigar a causa raiz do problema de timeout
"""
import asyncio
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://", 1)

async def investigate_contatos():
    """Investigar a tabela contatos"""
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"server_settings": {"statement_timeout": "1800000"}}  # 30 minutos
    )

    async with engine.begin() as conn:
        # Verificar estrutura da tabela contatos
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'contatos'
            ORDER BY ordinal_position
        """))
        print("Estrutura da tabela contatos:")
        for row in result:
            print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")

        # Verificar índices
        result = await conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = 'contatos'
        """))
        print("\nÍndices da tabela contatos:")
        for row in result:
            print(f"  {row[0]}")

        # Verificar triggers
        result = await conn.execute(text("""
            SELECT trigger_name, event_manipulation, event_object_table
            FROM information_schema.triggers
            WHERE event_object_schema = 'public'
            AND event_object_table = 'contatos'
        """))
        print("\nTriggers da tabela contatos:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")

        # Verificar constraints
        result = await conn.execute(text("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_schema = 'public'
            AND table_name = 'contatos'
        """))
        print("\nConstraints da tabela contatos:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")

        # Verificar quantidade de registros
        result = await conn.execute(text("SELECT COUNT(*) FROM contatos"))
        count = result.scalar()
        print(f"\nQuantidade de registros na tabela contatos: {count}")

        # Verificar tamanho médio dos arrays
        result = await conn.execute(text("""
            SELECT 
                AVG(array_length(telefones, 1)) as avg_telefones,
                AVG(array_length(celulares, 1)) as avg_celulares,
                MAX(array_length(telefones, 1)) as max_telefones,
                MAX(array_length(celulares, 1)) as max_celulares
            FROM contatos
        """))
        print("\nEstatísticas dos arrays:")
        for row in result:
            print(f"  Média telefones: {row[0]}")
            print(f"  Média celulares: {row[1]}")
            print(f"  Máximo telefones: {row[2]}")
            print(f"  Máximo celulares: {row[3]}")

        # Verificar registros com arrays grandes
        result = await conn.execute(text("""
            SELECT empresa_id, array_length(telefones, 1) as num_telefones, 
                   array_length(celulares, 1) as num_celulares
            FROM contatos
            WHERE array_length(telefones, 1) > 10 OR array_length(celulares, 1) > 10
            LIMIT 10
        """))
        print("\nRegistros com arrays grandes (>10 elementos):")
        for row in result:
            print(f"  Empresa ID: {row[0]}, Telefones: {row[1]}, Celulares: {row[2]}")

    await engine.dispose()

async def investigate_registrations():
    """Investigar a tabela registrations"""
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"server_settings": {"statement_timeout": "1800000"}}  # 30 minutos
    )

    async with engine.begin() as conn:
        # Verificar estrutura da tabela registrations
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'registrations'
            ORDER BY ordinal_position
        """))
        print("Estrutura da tabela registrations:")
        for row in result:
            print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")

        # Verificar índices
        result = await conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            AND tablename = 'registrations'
        """))
        print("\nÍndices da tabela registrations:")
        for row in result:
            print(f"  {row[0]}")

        # Verificar constraints
        result = await conn.execute(text("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_schema = 'public'
            AND table_name = 'registrations'
        """))
        print("\nConstraints da tabela registrations:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")

        # Verificar quantidade de registros
        result = await conn.execute(text("SELECT COUNT(*) FROM registrations"))
        count = result.scalar()
        print(f"\nQuantidade de registros na tabela registrations: {count}")

    await engine.dispose()

async def investigate_csv_data():
    """Investigar os dados do CSV"""
    print("\nInvestigando dados do CSV...")
    
    # Ler o CSV normalizado
    df = pd.read_csv('data/processed/emplacamentos_normalized.csv', nrows=1000)
    
    # Verificar estatísticas dos arrays
    print("\nEstatísticas dos arrays no CSV (primeiras 1000 linhas):")
    print(f"  Telefones não-null: {df['telefones'].notna().sum()}")
    print(f"  Celulares não-null: {df['celulares'].notna().sum()}")
    
    # Verificar tamanho dos arrays
    df['num_telefones'] = df['telefones'].apply(lambda x: len(x) if isinstance(x, list) else 0)
    df['num_celulares'] = df['celulares'].apply(lambda x: len(x) if isinstance(x, list) else 0)
    
    print(f"  Média telefones: {df['num_telefones'].mean():.2f}")
    print(f"  Média celulares: {df['num_celulares'].mean():.2f}")
    print(f"  Máximo telefones: {df['num_telefones'].max()}")
    print(f"  Máximo celulares: {df['num_celulares'].max()}")
    
    # Verificar registros com arrays grandes
    large_arrays = df[(df['num_telefones'] > 10) | (df['num_celulares'] > 10)]
    print(f"\nRegistros com arrays grandes (>10 elementos): {len(large_arrays)}")
    if len(large_arrays) > 0:
        print(large_arrays[['empresa_id', 'num_telefones', 'num_celulares']].head(10).to_string())

if __name__ == "__main__":
    print("=" * 80)
    print("INVESTIGAÇÃO DA CAUSA RAIZ DO PROBLEMA DE TIMEOUT")
    print("=" * 80)
    
    asyncio.run(investigate_contatos())
    print("\n" + "=" * 80)
    asyncio.run(investigate_registrations())
    print("\n" + "=" * 80)
    investigate_csv_data()
    print("\n" + "=" * 80)
