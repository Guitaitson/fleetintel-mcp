#!/usr/bin/env python3
"""
GT-29: Validação e Refresh
Valida integridade dos dados e atualiza views materializadas
"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from datetime import datetime

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+asyncpg://", 1)
engine = create_async_engine(DATABASE_URL, echo=False)

async def validate_data():
    """Valida integridade dos dados"""
    print("=" * 60)
    print("✅ GT-29: VALIDAÇÃO E REFRESH")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    async with engine.connect() as conn:
        # 1. Contagem total
        result = await conn.execute(text("SELECT COUNT(*) FROM registrations"))
        total = result.scalar()
        print(f"\n📊 Total de registros: {total:,}")
        
        # 2. Duplicatas
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT chassi, data_emplacamento, COUNT(*) 
                FROM registrations 
                WHERE chassi IS NOT NULL AND data_emplacamento IS NOT NULL
                GROUP BY chassi, data_emplacamento 
                HAVING COUNT(*) > 1
            ) duplicates
        """))
        duplicates = result.scalar()
        print(f"🔍 Duplicatas encontradas: {duplicates}")
        
        # 3. Distribuição por marca
        result = await conn.execute(text("""
            SELECT marca, COUNT(*) as total 
            FROM registrations 
            WHERE marca IS NOT NULL
            GROUP BY marca 
            ORDER BY total DESC 
            LIMIT 5
        """))
        print(f"\n📈 Top 5 marcas:")
        for row in result:
            print(f"   - {row[0]}: {row[1]:,}")
        
        # 4. Refresh views materializadas
        print(f"\n🔄 Refreshing views materializadas...")
        await conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY registration_summary"))
        await conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_stats"))
        await conn.commit()
        print(f"✅ Views atualizadas!")
    
    print(f"\n🎉 Validação concluída com sucesso!")

if __name__ == "__main__":
    asyncio.run(validate_data())
