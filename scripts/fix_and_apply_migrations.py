#!/usr/bin/env python3
"""
Script para corrigir conflitos e aplicar migrações pendentes
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from fleet_intel_mcp.db.connection import engine
from datetime import datetime


async def fix_and_apply():
    """Corrige conflitos e aplica migrações"""
    
    print("=" * 60)
    print("🔧 CORREÇÃO E APLICAÇÃO DE MIGRAÇÕES")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    async with engine.begin() as conn:
        # 1. Remover função antiga upsert_registration (da migração 02)
        print("📋 Passo 1: Removendo função antiga upsert_registration...")
        try:
            await conn.execute(text("""
                DROP FUNCTION IF EXISTS upsert_registration(TEXT, JSONB);
            """))
            print("✅ Função antiga removida com sucesso!")
        except Exception as e:
            print(f"⚠️  Aviso ao remover função: {e}")
        
        print()
        
        # 2. Aplicar migração 09 (funções UPSERT completas)
        print("📋 Passo 2: Aplicando migração 09 (funções UPSERT)...")
        try:
            migration_file = Path(__file__).parent.parent / "supabase" / "migrations" / "20260103000009_upsert_functions.sql"
            with open(migration_file, "r", encoding="utf-8") as f:
                sql = f.read()
            
            # Executar SQL
            raw_conn = await conn.get_raw_connection()
            await raw_conn.driver_connection.execute(sql)
            print("✅ Migração 09 aplicada com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao aplicar migração 09: {e}")
            raise
        
        print()
        
        # 3. Verificar funções criadas
        print("📋 Passo 3: Verificando funções criadas...")
        result = await conn.execute(text("""
            SELECT 
                proname,
                pg_get_function_identity_arguments(oid) as args
            FROM pg_proc 
            WHERE proname LIKE 'upsert_registration%'
            ORDER BY proname
        """))
        
        functions = result.fetchall()
        print(f"✅ Funções encontradas: {len(functions)}")
        for func in functions:
            print(f"   - {func.proname}({func.args})")
        
        print()
        
        # 4. Registrar todas as migrações na tabela _migrations
        print("📋 Passo 4: Registrando migrações na tabela _migrations...")
        
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
        
        # 5. Verificar estado final
        print("📊 Passo 5: Verificando estado final...")
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM _migrations
        """))
        count = result.scalar()
        print(f"✅ Total de migrações registradas: {count}")
    
    print()
    print("=" * 60)
    print("🎉 CORREÇÃO E APLICAÇÃO CONCLUÍDAS COM SUCESSO!")
    print("=" * 60)
    print()
    print("📋 Próximo passo: Execute 'make db-health' para validar")


if __name__ == "__main__":
    asyncio.run(fix_and_apply())
