#!/usr/bin/env python3
"""
Teste do ETL otimizado com 10.000 registros
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from load_normalized_schema_optimized_v2 import load_data

async def main():
    print("=" * 60)
    print("TESTE ETL OTIMIZADO - 10.000 REGISTROS")
    print("=" * 60)
    
    # Modificar para ler 10.000 registros
    import pandas as pd
    
    DTYPE_MAP = {
        'cpf_cnpj_proprietario': str,
        'cnpj_concessionario': str,
        'cep': str,
        'cod_atividade_economica_norm': str,
        'chassi': str,
        'placa': str
    }
    
    print("\nLendo CSV (10.000 registros)...")
    df = pd.read_csv("data/processed/emplacamentos_normalized.csv", 
                     sep=';', encoding='utf-8', 
                     nrows=10000, 
                     dtype=DTYPE_MAP)
    
    print(f"Total: {len(df)} registros")
    
    # Salvar arquivo temporario
    temp_file = "data/processed/test_10k.csv"
    df.to_csv(temp_file, sep=';', index=False, encoding='utf-8')
    print(f"Arquivo temporario criado: {temp_file}")
    
    # Executar carga
    result = await load_data(temp_file, test_mode=False)
    
    print(f"\n" + "=" * 60)
    print("TESTE CONCLUIDO")
    print(f"Registrations inseridos: {result['success']}")
    print(f"Erros: {result['errors']}")
    print(f"Tempo: {int(result['duration']/60)}min {int(result['duration']%60)}s")
    print(f"Taxa: {int(result['success']/result['duration'])} reg/s")
    print("=" * 60)
    
    # Limpar arquivo temporario
    if os.path.exists(temp_file):
        os.remove(temp_file)
        print(f"\nArquivo temporario removido: {temp_file}")

if __name__ == "__main__":
    asyncio.run(main())
