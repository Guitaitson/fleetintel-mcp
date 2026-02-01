#!/usr/bin/env python3
"""
Script para corrigir o estado das migrações
Registra migrações já aplicadas e aplica funções faltantes
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from fleet_intel_mcp.db.connection import engine
from datetime import datetime


async def check_and_fix():
    """Verifica e corrige estado das migrações"""
    
    print("=" * 60)
    print("🔧 CORREÇÃO DO ESTADO DAS MIGRAÇÕES")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    async with engine.begin() as conn:
        # 1. Verificar função upsert_registrations_batch
        print("📋 Verificando função upsert_registrations_batch...")
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM pg_proc 
            WHERE proname = 'upsert_registrations_batch'
        """))
        exists = result.scalar() > 0
        
        if not exists:
            print("❌ Função não encontrada. Aplicando migração 09...")
            
            # Ler e aplicar migração 09
            migration_file = Path(__file__).parent.parent / "supabase" / "migrations" / "20260103000009_upsert_functions.sql"
            with open(migration_file, "r", encoding="utf-8") as f:
                sql = f.read()
            
            # Executar SQL
            raw_conn = await conn.get_raw_connection()
            await raw_conn.driver_connection.execute(sql)
            print("✅ Migração 09 aplicada com sucesso!")
        else:
            print("✅ Função já existe!")
        
        print()
        
        # 2. Registrar todas as migrações aplicadas
        print("📋 Registrando migrações na tabela _migrations...")
        
        migrations = [
            "20260103000001_create_registrations.sql",
            "20260103000002_deduplicate_registrations.sql",
            "20260103000003_add_indexes.sql",
            "20260103000004_auxiliary_tables.sql",
            "20260103000005_materialized_views.sql",
            "20260103000006_maintenance.sql",
            "20260103000007_enable_rls.sql",
            "20260103000008_fix_postgrest_permissions.sql",
            "20260103000009_upsert_functions.sql",
        ]
        
        for migration in migrations:
            # Verificar se já está registrada
            result = await conn.execute(
                text("SELECT 1 FROM _migrations WHERE filename = :filename"),
                {"filename": migration}
            )
            
            if result.scalar():
                print(f"  ⏭️  {migration} - já registrada")
            else:
                # Registrar migração
                await conn.execute(
                    text("INSERT INTO _migrations (filename, executed_at) VALUES (:filename, NOW())"),
                    {"filename": migration}
                )
                print(f"  ✅ {migration} - registrada")
        
        print()
        
        # 3. Verificar estado final
        print("📊 Estado final das migrações:")
        result = await conn.execute(text("""
            SELECT filename, executed_at 
            FROM _migrations 
            ORDER BY executed_at
        """))
        
        migrations_registered = result.fetchall()
        print(f"✅ Total de migrações registradas: {len(migrations_registered)}")
        for mig in migrations_registered:
            print(f"   - {mig.filename}")
    
    print()
    print("=" * 60)
    print("🎉 CORREÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_and_fix())
