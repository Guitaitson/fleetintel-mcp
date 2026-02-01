#!/usr/bin/env python3
"""
Script de manutenção do banco de dados
Executa VACUUM ANALYZE e refresh de views materializadas
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from fleet_intel_mcp.db.connection import engine
from datetime import datetime


async def run_maintenance():
    """Executa manutenção completa do banco"""
    
    print("=" * 60)
    print("🔧 MANUTENÇÃO DO BANCO DE DADOS")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # 1. VACUUM ANALYZE
    print("📋 Passo 1: Executando VACUUM ANALYZE...")
    try:
        # VACUUM não pode ser executado dentro de uma transação
        async with engine.connect() as conn:
            await conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                text("VACUUM ANALYZE registrations")
            )
        print("✅ VACUUM ANALYZE concluído!")
    except Exception as e:
        print(f"⚠️  Aviso: {e}")
    
    print()
    
    # 2. Refresh Views Materializadas
    print("📋 Passo 2: Atualizando views materializadas...")
    try:
        async with engine.begin() as conn:
            # Verificar se a função existe
            result = await conn.execute(text("""
                SELECT COUNT(*) 
                FROM pg_proc 
                WHERE proname = 'refresh_materialized_views_concurrently'
            """))
            
            if result.scalar() > 0:
                await conn.execute(text("SELECT refresh_materialized_views_concurrently()"))
                print("✅ Views materializadas atualizadas!")
            else:
                print("⚠️  Função refresh_materialized_views_concurrently não encontrada")
    except Exception as e:
        print(f"⚠️  Aviso: {e}")
    
    print()
    
    # 3. Estatísticas
    print("📋 Passo 3: Coletando estatísticas...")
    try:
        async with engine.begin() as conn:
            # Tamanho do banco
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
            
            # Número de registros
            result = await conn.execute(text("SELECT COUNT(*) FROM registrations"))
            count = result.scalar()
            print(f"📊 Total de registros: {count:,}")
    except Exception as e:
        print(f"⚠️  Erro ao coletar estatísticas: {e}")
    
    print()
    print("=" * 60)
    print("🎉 MANUTENÇÃO CONCLUÍDA!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_maintenance())
