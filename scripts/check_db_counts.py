#!/usr/bin/env python3
"""
Verificar contagem de registros no banco de dados
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+asyncpg://', 1)
engine = create_async_engine(DATABASE_URL, echo=False)

async def check_counts():
    async with engine.begin() as conn:
        tables = ['marcas', 'modelos', 'vehicles', 'empresas', 'enderecos', 'contatos', 'registrations']
        print("=" * 60)
        print("CONTAGEM DE REGISTROS NO BANCO DE DADOS")
        print("=" * 60)
        for table in tables:
            result = await conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
            count = result.scalar()
            print(f"{table:20s}: {count:>15,}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_counts())
