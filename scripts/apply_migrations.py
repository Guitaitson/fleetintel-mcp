#!/usr/bin/env python3
"""
Script simplificado para aplicar migrações
"""
import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Criar engine diretamente
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL não encontrada no .env")
    sys.exit(1)

# Converter para formato asyncpg se necessário
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)


async def apply_migrations():
    """Aplica migrações pendentes"""
    
    print("=" * 60)
    print("🔄 APLICANDO MIGRAÇÕES")
    print("=" * 60)
    
    migrations_dir = Path(__file__).parent.parent / "supabase" / "migrations"
    
    # Listar arquivos de migração
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    async with engine.begin() as conn:
        # Verificar quais migrações já foram aplicadas
        result = await conn.execute(
            text("SELECT filename FROM _migrations ORDER BY executed_at")
        )
        applied_migrations = {row[0] for row in result.fetchall()}
        
        print(f"\n✅ Migrações já aplicadas: {len(applied_migrations)}")
        for mig in sorted(applied_migrations):
            print(f"   - {mig}")
        
        # Aplicar migrações pendentes
        pending = []
        for migration_file in migration_files:
            if migration_file.name not in applied_migrations:
                pending.append(migration_file)
        
        print(f"\n📋 Migrações pendentes: {len(pending)}")
        
        if not pending:
            print("\n✅ Todas as migrações já foram aplicadas!")
            return
        
        for migration_file in pending:
            print(f"\n🔄 Aplicando: {migration_file.name}")
            
            # Ler SQL
            with open(migration_file, "r", encoding="utf-8") as f:
                sql = f.read()
            
            try:
                # Executar SQL
                raw_conn = await conn.get_raw_connection()
                await raw_conn.driver_connection.execute(sql)
                
                # Registrar migração
                await conn.execute(
                    text("INSERT INTO _migrations (filename, executed_at) VALUES (:filename, NOW())"),
                    {"filename": migration_file.name}
                )
                
                print(f"✅ {migration_file.name} aplicada com sucesso!")
                
            except Exception as e:
                print(f"❌ Erro ao aplicar {migration_file.name}: {e}")
                raise
        
        print("\n" + "=" * 60)
        print(f"🎉 {len(pending)} migração(ões) aplicada(s) com sucesso!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(apply_migrations())
