#!/usr/bin/env python3
"""
Testar inserção na tabela marcas
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL').replace('postgresql://', 'postgresql+asyncpg://', 1)
engine = create_async_engine(DATABASE_URL, echo=False, connect_args={'server_settings': {'statement_timeout': '300000'}})

async def check_marcas():
    async with engine.begin() as conn:
        # Verificar se tabela existe
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM marcas
        """))
        count = result.scalar()
        print(f'Contagem atual de marcas: {count}')
        
        # Tentar um INSERT simples
        try:
            await conn.execute(text("""
                INSERT INTO marcas (nome) VALUES ('TESTE_TIMEOUT')
                ON CONFLICT (nome) DO NOTHING
            """))
            print('INSERT simples funcionou!')
        except Exception as e:
            print(f'ERRO no INSERT simples: {e}')
        
        # Tentar INSERT em batch
        try:
            params = [{'nome': 'TESTE1'}, {'nome': 'TESTE2'}, {'nome': 'TESTE3'}]
            await conn.execute(text("""
                INSERT INTO marcas (nome)
                VALUES (:nome)
                ON CONFLICT (nome) DO NOTHING
            """), params)
            print('INSERT em batch funcionou!')
        except Exception as e:
            print(f'ERRO no INSERT em batch: {e}')

if __name__ == "__main__":
    asyncio.run(check_marcas())
