import os
import sys
import asyncio
from sqlalchemy import text

# Adicionar diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fleet_intel_mcp.db.connection import engine

async def run_migrations():
    migrations_dir = "supabase/migrations"
    migrations = sorted(os.listdir(migrations_dir))
    
    async with engine.begin() as conn:
        # Criar tabela de controle de migrações se não existir
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id SERIAL PRIMARY KEY,
                filename TEXT UNIQUE NOT NULL,
                executed_at TIMESTAMP DEFAULT NOW()
            );
        """))
        
        # Executar migrações pendentes
        for migration in migrations:
            if not migration.endswith(".sql"):
                continue
                
            # Verificar se migração já foi aplicada
            result = await conn.execute(
                text("SELECT 1 FROM _migrations WHERE filename = :filename"),
                {"filename": migration}
            )
            if result.scalar():
                print(f"✅ Migração já aplicada: {migration}")
                continue
                
            # Executar migração
            with open(os.path.join(migrations_dir, migration), "r", encoding="utf-8") as f:
                sql = f.read()
                # Acessar conexão raw do asyncpg diretamente
                raw_conn = await conn.get_raw_connection()
                await raw_conn.driver_connection.execute(sql)
                
            # Registrar migração
            await conn.execute(
                text("INSERT INTO _migrations (filename) VALUES (:filename)"),
                {"filename": migration}
            )
            print(f"✅ Migração aplicada: {migration}")

if __name__ == "__main__":
    asyncio.run(run_migrations())
