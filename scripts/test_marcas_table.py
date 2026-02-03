#!/usr/bin/env python3
"""
Script para testar a tabela marcas e identificar problemas
"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://", 1)

async def test_marcas_table():
    """Testar a tabela marcas"""
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"server_settings": {"statement_timeout": "1800000"}}  # 30 minutos
    )

    async with engine.begin() as conn:
        # Verificar se a tabela marcas existe
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'marcas'
            )
        """))
        exists = result.scalar()
        print(f"Tabela marcas existe: {exists}")

        if exists:
            # Verificar estrutura da tabela
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'marcas'
                ORDER BY ordinal_position
            """))
            print("\nEstrutura da tabela marcas:")
            for row in result:
                print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")

            # Verificar índices
            result = await conn.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = 'marcas'
            """))
            print("\nÍndices da tabela marcas:")
            for row in result:
                print(f"  {row[0]}")

            # Verificar triggers
            result = await conn.execute(text("""
                SELECT trigger_name, event_manipulation, event_object_table
                FROM information_schema.triggers
                WHERE event_object_schema = 'public'
                AND event_object_table = 'marcas'
            """))
            print("\nTriggers da tabela marcas:")
            for row in result:
                print(f"  {row[0]}: {row[1]}")

            # Verificar constraints
            result = await conn.execute(text("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_schema = 'public'
                AND table_name = 'marcas'
            """))
            print("\nConstraints da tabela marcas:")
            for row in result:
                print(f"  {row[0]}: {row[1]}")

            # Verificar quantidade de registros
            result = await conn.execute(text("SELECT COUNT(*) FROM marcas"))
            count = result.scalar()
            print(f"\nQuantidade de registros na tabela marcas: {count}")

            # Tentar inserir uma marca de teste
            print("\nTentando inserir uma marca de teste...")
            try:
                await conn.execute(text("""
                    INSERT INTO marcas (nome)
                    VALUES ('TESTE_MARCA')
                    ON CONFLICT (nome) DO NOTHING
                """))
                print("Inserção de teste bem-sucedida!")

                # Remover marca de teste
                await conn.execute(text("DELETE FROM marcas WHERE nome = 'TESTE_MARCA'"))
                print("Marca de teste removida!")
            except Exception as e:
                print(f"Erro ao inserir marca de teste: {e}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_marcas_table())
