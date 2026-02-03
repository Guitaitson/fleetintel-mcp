#!/usr/bin/env python3
"""
Script para verificar locks no banco de dados
"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://", 1)

async def check_locks():
    """Verificar locks no banco de dados"""
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
        # Verificar locks ativos
        result = await conn.execute(text("""
            SELECT
                l.locktype,
                l.database,
                l.relation,
                l.page,
                l.tuple,
                l.virtualxid,
                l.transactionid,
                l.classid,
                l.objid,
                l.objsubid,
                l.virtualtransaction,
                l.pid,
                l.mode,
                l.granted,
                a.usename,
                a.query,
                a.query_start,
                age(now(), a.query_start) AS "age"
            FROM pg_locks l
            LEFT JOIN pg_stat_activity a ON l.pid = a.pid
            WHERE NOT l.granted
            ORDER BY a.query_start
        """))
        print("Locks não concedidos:")
        for row in result:
            print(f"  {row}")

        # Verificar locks na tabela marcas
        result = await conn.execute(text("""
            SELECT
                l.locktype,
                l.mode,
                l.granted,
                a.usename,
                a.query,
                a.query_start,
                age(now(), a.query_start) AS "age"
            FROM pg_locks l
            LEFT JOIN pg_stat_activity a ON l.pid = a.pid
            JOIN pg_class c ON l.relation = c.oid
            WHERE c.relname = 'marcas'
            ORDER BY a.query_start
        """))
        print("\nLocks na tabela marcas:")
        for row in result:
            print(f"  {row}")

        # Verificar transações ativas
        result = await conn.execute(text("""
            SELECT
                pid,
                usename,
                application_name,
                client_addr,
                state,
                query_start,
                state_change,
                waiting,
                xact_start,
                query,
                age(now(), query_start) AS "age"
            FROM pg_stat_activity
            WHERE state != 'idle'
            ORDER BY query_start
        """))
        print("\nTransações ativas:")
        for row in result:
            print(f"  {row}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_locks())
