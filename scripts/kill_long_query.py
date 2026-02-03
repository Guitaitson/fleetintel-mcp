#!/usr/bin/env python3
"""
Script para matar queries longas que estão bloqueando o banco
"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://", 1)

async def kill_long_queries():
    """Matar queries longas"""
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"server_settings": {"statement_timeout": "1800000"}}  # 30 minutos
    )

    async with engine.begin() as conn:
        # Verificar queries longas
        result = await conn.execute(text("""
            SELECT
                pid,
                usename,
                application_name,
                state,
                query_start,
                state_change,
                xact_start,
                query,
                age(now(), query_start) AS "age"
            FROM pg_stat_activity
            WHERE state != 'idle'
            AND age(now(), query_start) > interval '10 minutes'
            ORDER BY query_start
        """))
        print("Queries longas (mais de 10 minutos):")
        long_queries = []
        for row in result:
            print(f"  PID: {row[0]}, User: {row[1]}, Age: {row[8]}")
            print(f"  Query: {row[7][:100]}...")
            long_queries.append(row[0])

        # Matar queries longas
        if long_queries:
            print(f"\nMatando {len(long_queries)} queries longas...")
            for pid in long_queries:
                try:
                    await conn.execute(text(f"SELECT pg_terminate_backend({pid})"))
                    print(f"  Query com PID {pid} terminada")
                except Exception as e:
                    print(f"  Erro ao terminar query com PID {pid}: {e}")
        else:
            print("\nNenhuma query longa encontrada")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(kill_long_queries())
