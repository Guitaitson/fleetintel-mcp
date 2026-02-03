"""
Script de diagnóstico para investigar o erro de tipo de dados no normalize_data_optimized.py
"""

import pandas as pd
import sys

# Caminho do arquivo CSV normalizado
input_path = 'data/processed/emplacamentos_normalized.csv'

print("=" * 80)
print("DIAGNÓSTICO: Investigando erro de tipo de dados")
print("=" * 80)

# Ler CSV
print(f"\n[INFO] Lendo: {input_path}")
df = pd.read_csv(input_path, sep=';', encoding='utf-8', dtype=str)
print(f"[OK] {len(df):,} registros lidos")

# Verificar colunas críticas
print("\n[INFO] Verificando colunas críticas...")
string_columns = ['cpf_cnpj_proprietario', 'cnpj_concessionario', 'cep',
                  'cod_atividade_economica_norm', 'chassi', 'placa']

for col in string_columns:
    if col in df.columns:
        print(f"   [OK] Coluna '{col}' existe")
        
        # Verificar tipo de dado
        dtype = df[col].dtype
        print(f"        Tipo: {dtype}")
        
        # Verificar se é uma Series
        print(f"        É Series: {isinstance(df[col], pd.Series)}")
        
        # Verificar se é um DataFrame
        print(f"        É DataFrame: {isinstance(df[col], pd.DataFrame)}")
        
        # Verificar alguns valores
        print(f"        Exemplo de valores:")
        for i, val in enumerate(df[col].head(3)):
            print(f"          [{i}] {repr(val)} (tipo: {type(val).__name__})")
        
        # Verificar se há valores com ".0"
        has_dot_zero = df[col].str.endswith('.0', na=False).any()
        print(f"        Tem valores com '.0': {has_dot_zero}")
        
        # Tentar remover ".0"
        try:
            df_test = df[col].astype(str).str.replace(r'\.0$', '', regex=True)
            print(f"        [OK] Remoção de '.0' funcionou")
        except Exception as e:
            print(f"        [ERRO] Remoção de '.0' falhou: {e}")
    else:
        print(f"   [ERRO] Coluna '{col}' NÃO existe!")

# Verificar colunas que deveriam existir mas não existem
print("\n[INFO] Colunas que deveriam existir mas não existem:")
missing_cols = [col for col in string_columns if col not in df.columns]
if missing_cols:
    for col in missing_cols:
        print(f"   [ERRO] '{col}' não existe")
else:
    print("   [OK] Todas as colunas existem")

# Listar todas as colunas do DataFrame
print("\n[INFO] Todas as colunas do DataFrame:")
for i, col in enumerate(df.columns):
    print(f"   [{i}] {col}")

print("\n" + "=" * 80)
print("DIAGNÓSTICO CONCLUÍDO")
print("=" * 80)
