#!/usr/bin/env python3
"""Valida configuração de ambiente antes de iniciar a aplicação"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.settings import get_settings
from pydantic import ValidationError
import asyncio

async def validate_supabase():
    """Testa conexão com Supabase"""
    print("🔍 Testando Supabase...")
    try:
        from supabase import create_client
        settings = get_settings()
        
        client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key
        )
        
        # Teste simples
        result = client.table("_health").select("*").limit(1).execute()
        print("✅ Supabase: OK")
        return True
    except Exception as e:
        print(f"❌ Supabase: ERRO - {e}")
        return False

async def validate_redis():
    """Testa conexão com Redis"""
    print("🔍 Testando Redis...")
    try:
        import redis.asyncio as redis
        settings = get_settings()
        
        client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password.get_secret_value() if settings.redis_password else None,
            db=settings.redis_db,
            decode_responses=True
        )
        
        await client.ping()
        print("✅ Redis: OK")
        await client.close()
        return True
    except Exception as e:
        print(f"❌ Redis: ERRO - {e}")
        return False

def validate_settings():
    """Valida settings"""
    print("🔍 Validando variáveis de ambiente...")
    try:
        settings = get_settings()
        print(f"✅ Settings: OK")
        print(f"   - Environment: {settings.environment}")
        print(f"   - Debug: {settings.debug}")
        print(f"   - Log Level: {settings.log_level}")
        return True
    except ValidationError as e:
        print(f"❌ Settings: ERRO DE VALIDAÇÃO")
        print(e)
        return False

async def main():
    print("=" * 60)
    print("FleetIntel MCP - Validação de Ambiente")
    print("=" * 60)
    print()
    
    results = []
    
    # Validar settings
    results.append(validate_settings())
    print()
    
    # Validar Supabase
    results.append(await validate_supabase())
    print()
    
    # Validar Redis
    results.append(await validate_redis())
    print()
    
    print("=" * 60)
    if all(results):
        print("✅ TODOS OS TESTES PASSARAM")
        print("=" * 60)
        return 0
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
