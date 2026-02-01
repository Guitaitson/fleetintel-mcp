#!/usr/bin/env python3
"""Teste direto de conexão com asyncpg"""
import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv()

async def test_direct():
    DATABASE_URL = os.getenv("DATABASE_URL")
    print(f"🔍 Testando conexão direta com asyncpg...")
    print(f"   URL: postgresql://postgres.oqupslyezdxegyewwdsz:***@aws-1-us-east-1.pooler.supabase.com:5432/postgres")
    
    try:
        # Extrair componentes da URL
        # Format: postgresql://user:pass@host:port/db
        parts = DATABASE_URL.replace("postgresql://", "").split("@")
        user_pass = parts[0].split(":")
        user = user_pass[0]
        password = user_pass[1]
        
        host_db = parts[1].split("/")
        host_port = host_db[0].split(":")
        host = host_port[0]
        port = int(host_port[1])
        database = host_db[1]
        
        print(f"\n📋 Parâmetros de conexão:")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   User: {user}")
        print(f"   Database: {database}")
        print(f"   Password: {password[:10]}...")
        
        print(f"\n⏳ Conectando...")
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            timeout=10
        )
        
        print(f"✅ Conexão estabelecida!")
        
        # Testar query
        version = await conn.fetchval("SELECT version()")
        print(f"   PostgreSQL: {version[:80]}...")
        
        # Contar tabelas
        count = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        print(f"   Tabelas no schema public: {count}")
        
        # Listar algumas tabelas
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
            LIMIT 10
        """)
        print(f"\n📊 Primeiras tabelas:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        await conn.close()
        print(f"\n✅ Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro na conexão:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        import traceback
        print(f"\n📋 Traceback completo:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_direct())
