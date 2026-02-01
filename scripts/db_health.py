#!/usr/bin/env python3
"""
Health Check do Banco de Dados
Verifica o estado geral do banco de dados Supabase
"""
import asyncio
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from fleet_intel_mcp.db.connection import engine
from datetime import datetime


async def check_connection():
    """Verifica conexão com o banco"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        print("✅ Conexão com banco: OK")
        return True
    except Exception as e:
        print(f"❌ Conexão com banco: FALHOU - {e}")
        return False


async def check_tables():
    """Verifica existência das tabelas principais"""
    tables = [
        "registrations",
        "_migrations",
        "estados",
        "municipios",
        "categorias_veiculo",
        "marcas",
        "modelos",
    ]
    
    try:
        async with engine.begin() as conn:
            for table in tables:
                result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                )
                count = result.scalar()
                print(f"✅ Tabela '{table}': {count:,} registros")
        return True
    except Exception as e:
        print(f"❌ Verificação de tabelas: FALHOU - {e}")
        return False


async def check_materialized_views():
    """Verifica status das views materializadas"""
    views = [
        "estatisticas_por_estado",
        "estatisticas_por_municipio",
        "estatisticas_por_categoria",
    ]
    
    try:
        async with engine.begin() as conn:
            for view in views:
                # Verificar se view existe e tem dados
                result = await conn.execute(
                    text(f"SELECT COUNT(*) FROM {view}")
                )
                count = result.scalar()
                
                # Verificar última atualização (se possível)
                print(f"✅ View '{view}': {count:,} registros")
        return True
    except Exception as e:
        print(f"❌ Verificação de views: FALHOU - {e}")
        return False


async def check_indexes():
    """Verifica existência dos índices"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = 'registrations'
                ORDER BY indexname
            """))
            
            indexes = result.fetchall()
            print(f"✅ Índices na tabela 'registrations': {len(indexes)}")
            for idx in indexes:
                print(f"   - {idx.indexname}")
        return True
    except Exception as e:
        print(f"❌ Verificação de índices: FALHOU - {e}")
        return False


async def check_functions():
    """Verifica existência das funções"""
    functions = [
        "update_updated_at_column",
        "refresh_materialized_views_concurrently",
        "upsert_registration",
        "upsert_registrations_batch",
    ]
    
    try:
        async with engine.begin() as conn:
            for func in functions:
                result = await conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM pg_proc 
                    WHERE proname = '{func}'
                """))
                exists = result.scalar() > 0
                status = "✅" if exists else "❌"
                print(f"{status} Função '{func}': {'OK' if exists else 'NÃO ENCONTRADA'}")
        return True
    except Exception as e:
        print(f"❌ Verificação de funções: FALHOU - {e}")
        return False


async def check_database_size():
    """Verifica tamanho do banco de dados"""
    try:
        async with engine.begin() as conn:
            # Tamanho total do banco
            result = await conn.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """))
            db_size = result.scalar()
            print(f"📊 Tamanho do banco: {db_size}")
            
            # Tamanho da tabela principal
            result = await conn.execute(text("""
                SELECT pg_size_pretty(pg_total_relation_size('registrations'))
            """))
            table_size = result.scalar()
            print(f"📊 Tamanho da tabela 'registrations': {table_size}")
        return True
    except Exception as e:
        print(f"❌ Verificação de tamanho: FALHOU - {e}")
        return False


async def check_migrations():
    """Verifica migrações aplicadas"""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT filename, executed_at 
                FROM _migrations 
                ORDER BY executed_at DESC
                LIMIT 5
            """))
            
            migrations = result.fetchall()
            print(f"✅ Migrações aplicadas: {len(migrations)} (últimas 5)")
            for mig in migrations:
                print(f"   - {mig.filename} ({mig.executed_at.strftime('%Y-%m-%d %H:%M:%S')})")
        return True
    except Exception as e:
        print(f"❌ Verificação de migrações: FALHOU - {e}")
        return False


async def run_health_check():
    """Executa todos os checks"""
    print("=" * 60)
    print("🏥 HEALTH CHECK DO BANCO DE DADOS")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    checks = [
        ("Conexão", check_connection),
        ("Tabelas", check_tables),
        ("Views Materializadas", check_materialized_views),
        ("Índices", check_indexes),
        ("Funções", check_functions),
        ("Tamanho do Banco", check_database_size),
        ("Migrações", check_migrations),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Verificando: {name}")
        print("-" * 60)
        result = await check_func()
        results.append((name, result))
        print()
    
    # Resumo
    print("=" * 60)
    print("📊 RESUMO DO HEALTH CHECK")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {name}")
    
    print()
    print(f"Total: {passed}/{total} checks passaram")
    
    if passed == total:
        print("🎉 Todos os checks passaram! Banco de dados saudável.")
        return 0
    else:
        print("⚠️  Alguns checks falharam. Verifique os erros acima.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_health_check())
    sys.exit(exit_code)
