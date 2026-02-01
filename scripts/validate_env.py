import os
from dotenv import load_dotenv
import sys

def validate_env():
    """Valida variáveis de ambiente obrigatórias"""
    load_dotenv()  # Carrega variáveis do arquivo .env
    
    # Variáveis obrigatórias e suas descrições
    required_vars = {
        "VEHICLE_API_KEY": "Chave da API de veículos",
        "SUPABASE_URL": "URL do Supabase",
        "SUPABASE_SERVICE_KEY": "Chave de serviço do Supabase",
        "REDIS_HOST": "Host do Redis",
        "OPENAI_API_KEY": "Chave da API OpenAI"
    }
    
    missing = []
    invalid = []
    
    # Verifica presença e formato básico
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append((var, desc))
        elif value.startswith("your_") or "example" in value:
            invalid.append((var, "Valor parece ser placeholder"))
    
    # Exibe relatório
    print("\n=== VALIDAÇÃO DE VARIÁVEIS DE AMBIENTE ===")
    for var, desc in required_vars.items():
        status = "✅" if os.getenv(var) else "❌"
        print(f"{status} {var}: {desc}")
    
    # Erros detalhados
    if missing:
        print("\n🚨 VARIÁVEIS FALTANDO:")
        for var, desc in missing:
            print(f"- {var}: {desc}")
    
    if invalid:
        print("\n⚠️ VARIÁVEIS COM VALORES INVÁLIDOS:")
        for var, reason in invalid:
            print(f"- {var}: {reason}")
    
    # Resultado final
    if missing or invalid:
        print("\nStatus: FALHOU - Configure as variáveis corretamente")
        sys.exit(1)
    else:
        print("\nStatus: SUCESSO - Todas variáveis configuradas")
        sys.exit(0)

if __name__ == "__main__":
    validate_env()
