#!/usr/bin/env python3
"""
Script para verificar funções duplicadas no banco
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from fleet_intel_mcp.db.connection import engine


async def check_functions():
    """Verifica funções no banco"""
    
    print("=" * 60)
    print("🔍 VERIFICANDO FUNÇÕES NO BANCO")
    print("=" * 60)
    print()
    
    async with engine.begin() as conn:
        # Listar todas as funções upsert_registration
        result = await conn.execute(text("""
            SELECT 
                proname,
                pg_get_function_identity_arguments(oid) as args,
                prosrc
            FROM pg_proc 
            WHERE proname LIKE 'upsert_registration%'
            ORDER BY proname
        """))
        
        functions = result.fetchall()
        print(f"📋 Funções encontradas: {len(functions)}")
        print()
        
        for func in functions:
            print(f"Função: {func.proname}")
            print(f"Argumentos: {func.args}")
            print(f"Código (primeiras 200 chars): {func.prosrc[:200]}...")
            print("-" * 60)
            print()


if __name__ == "__main__":
    asyncio.run(check_functions())
