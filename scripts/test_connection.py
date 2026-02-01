#!/usr/bin/env python3
"""Teste de conexão com Supabase"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

async def test_connection():
    DATABASE_URL = os.getenv("DATABASE_URL")
    print(f"🔍 Testando conexão...")
    print(f"   URL: {DATABASE_URL[:50]}...")
    
    # Tentar com asyncpg
    try:
        async_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        engine = create_async_engine(async_url, echo=False)
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Conexão bem-sucedida!")
            print(f"   PostgreSQL: {version[:50]}...")
            
            # Testar contagem de tabelas
            result = await conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            count = result.scalar()
            print(f"   Tabelas no schema public: {count}")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão:")
        print(f"   {type(e).__name__}: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
