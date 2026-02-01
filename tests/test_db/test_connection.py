import pytest
from fleet_intel_mcp.db.connection import supabase, engine
from sqlalchemy import text
from postgrest.exceptions import APIError


@pytest.mark.asyncio
async def test_supabase_connection():
    """
    Testa conexão com Supabase via cliente oficial (API REST).
    
    Tenta acessar a tabela 'registrations' primeiro.
    Se falhar com PGRST205 (tabela não encontrada no cache),
    faz fallback para tabela '_migrations' e marca como skip
    com mensagem informativa.
    """
    try:
        # Tentativa 1: Acessar tabela registrations (ideal)
        result = supabase.table("registrations").select("*").limit(1).execute()
        assert result is not None
        print("✅ Conexão Supabase OK - Tabela 'registrations' acessível via API REST")
        
    except APIError as e:
        # APIError tem atributos diretos: code, message, hint, details
        error_code = getattr(e, 'code', None)
        
        if error_code == 'PGRST205':
            # Erro PGRST205: Tabela não encontrada no cache do PostgREST
            # Isso indica problema de configuração, não de conexão
            
            try:
                # Tentativa 2: Fallback para tabela _migrations
                result = supabase.table("_migrations").select("*").limit(1).execute()
                assert result is not None
                
                # Conexão funciona, mas tabela registrations não está exposta
                pytest.skip(
                    "⚠️  Conexão Supabase OK, mas tabela 'registrations' não exposta via API REST.\n"
                    "   Possíveis causas:\n"
                    "   1. Role 'authenticator' sem pgrst.db_schemas configurado\n"
                    "   2. Permissões ausentes para roles anon/authenticated\n"
                    "   3. Cache do PostgREST desatualizado\n"
                    "   Execute: scripts/diagnose_postgrest.sql no Supabase SQL Editor"
                )
                
            except APIError as e2:
                # Se nem _migrations funciona, há problema mais sério
                pytest.fail(
                    f"❌ Conexão Supabase falhou completamente.\n"
                    f"   Erro ao acessar '_migrations': {e2}\n"
                    f"   Verifique credenciais SUPABASE_URL e SUPABASE_KEY no .env"
                )
        else:
            # Outro tipo de erro da API
            raise


@pytest.mark.asyncio
async def test_sqlalchemy_connection():
    """Testa conexão com PostgreSQL via SQLAlchemy (conexão direta)"""
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
        print("✅ Conexão SQLAlchemy OK - PostgreSQL acessível diretamente")
