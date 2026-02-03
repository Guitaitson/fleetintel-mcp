#!/usr/bin/env python3
"""
Script para verificar contagens do banco de dados
"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://", 1)

async def check_counts():
    """Verificar contagens do banco de dados"""
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
        tables = ["marcas", "modelos", "vehicles", "empresas", "enderecos", "contatos", "registrations"]
        print("Contagens do banco de dados:")
        for table in tables:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table}: {count}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_counts())
