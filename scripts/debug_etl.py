#!/usr/bin/env python3
"""
Debug ETL - Verificar por que registrations falham
"""
import pandas as pd

# Ler 100 registros
df = pd.read_csv("data/processed/emplacamentos_normalized.csv", sep=';', encoding='utf-8', nrows=100)

print("=" * 60)
print("🔍 DEBUG Maps")
print("=" * 60)

# Simular vehicle_map
chassi_unicos = df['chassi'].dropna().nunique()
print(f"\n🚗 Chassi únicos: {chassi_unicos}")
print(f"   Total registros: {len(df)}")

# Simular empresa_map
empresas_df = df.groupby('cpf_cnpj_proprietario').first().reset_index()
empresas_df = empresas_df[empresas_df['cpf_cnpj_proprietario'].notna()]

print(f"\n🏢 Empresas agrupadas: {len(empresas_df)}")
print(f"   CNPJs não-nulos nos 100 registros: {df['cpf_cnpj_proprietario'].notna().sum()}")

# Criar map simulado
empresa_map = {}
for _, row in empresas_df.iterrows():
    cnpj_raw = row['cpf_cnpj_proprietario']
    if pd.notna(cnpj_raw):
        empresa_map[str(int(cnpj_raw))] = f"empresa_{len(empresa_map)}"

print(f"   Empresas no map: {len(empresa_map)}")
print(f"   Exemplo de chaves: {list(empresa_map.keys())[:5]}")

# Testar busca
print(f"\n🔍 Testando busca do primeiro registro:")
first_row = df.iloc[0]
print(f"   CNPJ original: {first_row['cpf_cnpj_proprietario']} (tipo: {type(first_row['cpf_cnpj_proprietario'])})")
cnpj_key = str(int(first_row['cpf_cnpj_proprietario'])) if pd.notna(first_row['cpf_cnpj_proprietario']) else None
print(f"   CNPJ convertido: '{cnpj_key}'")
print(f"   Existe no map? {cnpj_key in empresa_map}")

# Contar quantos vão falhar
failures = 0
for _, row in df.iterrows():
    chassi = row['chassi']
    cnpj_raw = row['cpf_cnpj_proprietario']
    
    if pd.isna(chassi):
        failures += 1
        continue
    
    cnpj_key = str(int(cnpj_raw)) if pd.notna(cnpj_raw) else None
    if not cnpj_key or cnpj_key not in empresa_map:
        failures += 1
        print(f"   ❌ Registro falhará - chassi: {chassi}, cnpj_key: {cnpj_key}, no map: {cnpj_key in empresa_map if cnpj_key else False}")
        if failures > 5:
            break

print(f"\n📊 Estimativa de falhas: {failures}+ de {len(df)}")
