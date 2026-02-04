"""
Script para limpar dados do banco de dados antes de uma nova carga.
Apaga todos os dados das tabelas na ordem correta (respeitando foreign keys).
"""

import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Carregar variaveis de ambiente
load_dotenv()

# Configuracoes
DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://", 1)


async def clean_database():
    """Limpa todas as tabelas do banco de dados."""
    print("=" * 60)
    print("LIMPEZA DO BANCO DE DADOS")
    print("=" * 60)
    
    engine = create_async_engine(DATABASE_URL, pool_size=5)
    
    # Ordem de limpeza (respeita foreign keys)
    tables = [
        'registrations',
        'contatos',
        'enderecos',
        'vehicles',
        'modelos',
        'marcas',
        'empresas',
    ]
    
    async with engine.begin() as conn:
        for table in tables:
            try:
                # Contar registros antes
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count_before = result.scalar()
                
                # Apagar registros
                await conn.execute(text(f"DELETE FROM {table}"))
                
                print(f"   {table}: {count_before:,} registros apagados")
            except Exception as e:
                print(f"   {table}: ERRO - {e}")
    
    await engine.dispose()
    
    print("\n[OK] Banco de dados limpo!")


if __name__ == "__main__":
    asyncio.run(clean_database())
