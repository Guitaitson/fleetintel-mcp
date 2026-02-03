"""
Script de diagnóstico para verificar tipos de dados no arquivo CSV raw
"""

import pandas as pd
import sys

# Caminho do arquivo CSV raw
input_path = 'data/processed/emplacamentos_raw.csv'

print("=" * 80)
print("DIAGNÓSTICO: Verificando tipos de dados no arquivo CSV RAW")
print("=" * 80)

# Ler CSV
print(f"\n[INFO] Lendo: {input_path}")
df = pd.read_csv(input_path, sep=';', encoding='utf-8')
print(f"[OK] {len(df):,} registros lidos")

# Verificar colunas críticas
print("\n[INFO] Verificando colunas críticas...")
critical_columns = {
    'DOCUMENTO': 'CNPJ/CPF do proprietário',
    'CNPJ CONCESSIONARIA': 'CNPJ da concessionária',
    'CEP': 'CEP',
    'CNAE AGRUPADO': 'CNAE agrupado',
    'CHASSI': 'Chassi',
    'PLACA': 'Placa'
}

for col, description in critical_columns.items():
    if col in df.columns:
        print(f"\n   [INFO] Coluna: {col} ({description})")
        
        # Verificar tipo de dado
        dtype = df[col].dtype
        print(f"        Tipo: {dtype}")
        
        # Verificar se é float64
        if dtype == 'float64':
            print(f"        [ALERTA] É float64 (deveria ser string/object)!")
            
            # Verificar quantos valores têm mais dígitos que o esperado
            if col == 'DOCUMENTO':
                # CNPJ: 14 dígitos
                long_values = df[col].astype(str).str.len() > 14
                count_long = long_values.sum()
                print(f"        Valores com >14 dígitos: {count_long:,} ({count_long/len(df)*100:.2f}%)")
                
                # Mostrar exemplos
                if count_long > 0:
                    print(f"        Exemplos de valores longos:")
                    for i, val in enumerate(df[col][long_values].head(3)):
                        print(f"          [{i}] {val} (len: {len(str(val))})")
            elif col == 'CEP':
                # CEP: 8 dígitos
                long_values = df[col].astype(str).str.len() > 8
                count_long = long_values.sum()
                print(f"        Valores com >8 dígitos: {count_long:,} ({count_long/len(df)*100:.2f}%)")
                
                # Mostrar exemplos
                if count_long > 0:
                    print(f"        Exemplos de valores longos:")
                    for i, val in enumerate(df[col][long_values].head(3)):
                        print(f"          [{i}] {val} (len: {len(str(val))})")
            elif col == 'CNAE AGRUPADO':
                # CNAE: 7 dígitos
                long_values = df[col].astype(str).str.len() > 7
                count_long = long_values.sum()
                print(f"        Valores com >7 dígitos: {count_long:,} ({count_long/len(df)*100:.2f}%)")
                
                # Mostrar exemplos
                if count_long > 0:
                    print(f"        Exemplos de valores longos:")
                    for i, val in enumerate(df[col][long_values].head(3)):
                        print(f"          [{i}] {val} (len: {len(str(val))})")
        else:
            print(f"        [OK] Não é float64")
    else:
        print(f"\n   [ERRO] Coluna '{col}' NÃO existe!")

print("\n" + "=" * 80)
print("DIAGNÓSTICO CONCLUÍDO")
print("=" * 80)
