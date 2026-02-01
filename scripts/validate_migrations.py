import asyncio
import sys
import os
from sqlalchemy import inspect, text

# Adicionar diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fleet_intel_mcp.db.connection import engine

async def validate_migrations():
    async with engine.connect() as conn:
        # Verificar tabela principal
        inspector = inspect(conn)
        tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())
        assert "registrations" in tables, "Tabela registrations não encontrada"
        
        # Verificar índices
        indexes = await conn.run_sync(
            lambda sync_conn: inspector.get_indexes("registrations")
        )
        required_indexes = {"registrations_external_id_idx"}
        existing_indexes = {index["name"] for index in indexes}
        assert required_indexes.issubset(existing_indexes), "Índices essenciais faltando"
        
        # Verificar views materializadas
        result = await conn.execute(
            text("SELECT matviewname FROM pg_matviews")
        )
        materialized_views = {row[0] for row in result}
        required_views = {
            "estatisticas_por_estado",
            "estatisticas_por_municipio",
            "estatisticas_por_categoria"
        }
        assert required_views.issubset(materialized_views), "Views materializadas faltando"
        
        # Verificar procedimentos
        result = await conn.execute(
            text("SELECT proname FROM pg_proc WHERE proname IN ('upsert_registration', 'refresh_materialized_views_concurrently')")
        )
        functions = {row[0] for row in result}
        assert len(functions) == 2, "Funções essenciais faltando"
        
        print("✅ Todas as migrações foram validadas com sucesso!")

if __name__ == "__main__":
    asyncio.run(validate_migrations())
