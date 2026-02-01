#!/usr/bin/env python3
"""
Script para verificar schema após migrations
"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

async def check_schema():
    DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.connect() as conn:
        print("=" * 60)
        print("🔍 VERIFICANDO SCHEMA NORMALIZADO")
        print("=" * 60)
        
        # Verificar tabelas
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('marcas', 'modelos', 'vehicles', 'empresas', 
                               'enderecos', 'contatos', 'registrations', 'cnae_lookup')
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        
        print(f"\n✅ Tabelas encontradas: {len(tables)}/8")
        for t in tables:
            print(f"   - {t}")
        
        # Verificar FKs
        result = await conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.table_constraints 
            WHERE table_schema = 'public' 
            AND constraint_type = 'FOREIGN KEY'
        """))
        fks = result.scalar()
        print(f"\n✅ Foreign Keys: {fks}")
        
        # Verificar funções
        result = await conn.execute(text("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_schema = 'public' 
            AND routine_name IN ('fix_documento', 'update_updated_at_column')
            ORDER BY routine_name
        """))
        funcs = [row[0] for row in result]
        print(f"\n✅ Funções: {len(funcs)}/2")
        for f in funcs:
            print(f"   - {f}()")
        
        # Testar função fix_documento
        print(f"\n🧪 Testando função fix_documento:")
        result = await conn.execute(text("""
            SELECT 
                fix_documento('2916265009116', 14) as cnpj_corrigido,
                fix_documento('4744099', 7) as cnae_corrigido,
                fix_documento('89010025', 8) as cep_ok
        """))
        row = result.fetchone()
        print(f"   CNPJ: {row[0]} (esperado: 02916265009116)")
        print(f"   CNAE: {row[1]} (esperado: 0474409)")
        print(f"   CEP:  {row[2]} (esperado: 89010025)")
        
        print("\n" + "=" * 60)
        if len(tables) == 8 and len(funcs) == 2:
            print("✅ SCHEMA NORMALIZADO PRONTO!")
            print("=" * 60)
            return True
        else:
            print("⚠️  Schema incompleto!")
            print("=" * 60)
            return False
    
    await engine.dispose()

if __name__ == "__main__":
    success = asyncio.run(check_schema())
    exit(0 if success else 1)
