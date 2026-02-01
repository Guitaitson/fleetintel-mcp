#!/usr/bin/env python3
"""
Script de validação da estrutura do CSV antes do ETL
"""
import pandas as pd
import sys

def validate_csv(csv_path: str, nrows: int = 100):
    print("=" * 60)
    print("🔍 VALIDAÇÃO DO CSV")
    print("=" * 60)
    
    # Ler CSV
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8', nrows=nrows)
    print(f"\n✅ CSV lido com sucesso: {len(df)} registros")
    print(f"   Total de colunas: {len(df.columns)}")
    
    # Verificar colunas obrigatórias
    required_cols = {
        'chassi': 'Identificador do veículo',
        'cpf_cnpj_proprietario': 'CNPJ da empresa',
        'data_emplacamento': 'Data do emplacamento',
        'marca': 'Marca do veículo',
        'modelo': 'Modelo do veículo'
    }
    
    print(f"\n📋 Verificando colunas obrigatórias:")
    missing = []
    for col, desc in required_cols.items():
        if col in df.columns:
            not_null = df[col].notna().sum()
            pct = (not_null / len(df)) * 100
            print(f"   ✅ {col:30} {not_null:>5}/{len(df)} ({pct:.1f}%) - {desc}")
        else:
            print(f"   ❌ {col:30} FALTANDO - {desc}")
            missing.append(col)
    
    if missing:
        print(f"\n❌ ERRO: Colunas obrigatórias faltando: {missing}")
        return False
    
    # Verificar tipos de dados
    print(f"\n🔍 Verificando tipos de dados:")
    print(f"   chassi: {df['chassi'].dtype}")
    print(f"   cpf_cnpj_proprietario: {df['cpf_cnpj_proprietario'].dtype}")
    print(f"   data_emplacamento: {df['data_emplacamento'].dtype}")
    
    # Mostrar exemplos de dados
    print(f"\n📊 Exemplos de dados (primeiros 3):")
    sample = df[['chassi', 'cpf_cnpj_proprietario', 'data_emplacamento', 'marca', 'modelo']].head(3)
    for idx, row in sample.iterrows():
        print(f"\n   Registro {idx}:")
        print(f"      chassi: {row['chassi']} (tipo: {type(row['chassi'])})")
        print(f"      cnpj: {row['cpf_cnpj_proprietario']} (tipo: {type(row['cpf_cnpj_proprietario'])})")
        print(f"      data: {row['data_emplacamento']} (tipo: {type(row['data_emplacamento'])})")
        print(f"      marca: {row['marca']}")
        print(f"      modelo: {row['modelo']}")
    
    # Verificar valores únicos
    print(f"\n📈 Estatísticas:")
    print(f"   Chassi únicos: {df['chassi'].nunique():,}")
    print(f"   CNPJs únicos: {df['cpf_cnpj_proprietario'].nunique():,}")
    print(f"   Marcas únicas: {df['marca'].nunique():,}")
    print(f"   Modelos únicos: {df['modelo'].nunique():,}")
    
    # Verificar CNPJs
    print(f"\n🔍 Validando CNPJs:")
    cnpjs_sample = df['cpf_cnpj_proprietario'].dropna().head(5)
    for cnpj in cnpjs_sample:
        cnpj_str = str(cnpj)
        # Remover decimais se for float
        if '.' in cnpj_str:
            cnpj_str = cnpj_str.split('.')[0]
        print(f"   {cnpj_str} (len: {len(cnpj_str)})")
    
    # Verificar datas
    print(f"\n📅 Validando datas de emplacamento:")
    try:
        df['data_parsed'] = pd.to_datetime(df['data_emplacamento'])
        print(f"   ✅ Datas parseadas com sucesso")
        print(f"   Exemplo: {df['data_parsed'].iloc[0]}")
    except Exception as e:
        print(f"   ❌ Erro ao parsear datas: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"✅ VALIDAÇÃO CONCLUÍDA")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    csv_path = "data/processed/emplacamentos_normalized.csv"
    nrows = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    
    validate_csv(csv_path, nrows)
