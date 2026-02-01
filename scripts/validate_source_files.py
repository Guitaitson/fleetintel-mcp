#!/usr/bin/env python3
"""
Script para validar arquivos fonte (Excel e CNAE)
"""
import pandas as pd
from pathlib import Path
import sys

def validate_excel():
    """Valida arquivo Excel de emplacamentos"""
    print("=" * 60)
    print("📋 VALIDANDO ARQUIVO EXCEL")
    print("=" * 60)
    
    excel_path = Path("Sample Emplacamentos.xlsx")
    
    if not excel_path.exists():
        print(f"❌ Arquivo não encontrado: {excel_path}")
        return False
    
    print(f"✅ Arquivo encontrado: {excel_path}")
    print(f"📊 Tamanho: {excel_path.stat().st_size / (1024*1024):.2f} MB")
    
    # Ler primeiras linhas
    print("\n🔍 Lendo estrutura do arquivo...")
    df = pd.read_excel(excel_path, nrows=5)
    
    print(f"\n✅ Colunas encontradas: {len(df.columns)}")
    print("\n📋 Lista de colunas:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    # Contar total de linhas (aproximado)
    print("\n🔍 Contando registros totais...")
    df_full = pd.read_excel(excel_path)
    total_rows = len(df_full)
    print(f"✅ Total de registros: {total_rows:,}")
    
    # Mostrar amostra
    print("\n📊 Amostra dos dados (primeiras 3 linhas):")
    print(df.head(3).to_string())
    
    return True, df.columns.tolist(), total_rows

def validate_cnae():
    """Valida arquivo CNAE"""
    print("\n" + "=" * 60)
    print("📋 VALIDANDO ARQUIVO CNAE")
    print("=" * 60)
    
    cnae_path = Path("CNAE_TRAT.csv")
    
    if not cnae_path.exists():
        print(f"❌ Arquivo não encontrado: {cnae_path}")
        return False
    
    print(f"✅ Arquivo encontrado: {cnae_path}")
    print(f"📊 Tamanho: {cnae_path.stat().st_size / (1024*1024):.2f} MB")
    
    # Ler arquivo
    print("\n🔍 Lendo estrutura do arquivo...")
    df = pd.read_csv(cnae_path, nrows=5)
    
    print(f"\n✅ Colunas encontradas: {len(df.columns)}")
    print("\n📋 Lista de colunas:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    # Contar total de linhas
    print("\n🔍 Contando registros totais...")
    df_full = pd.read_csv(cnae_path)
    total_rows = len(df_full)
    print(f"✅ Total de registros: {total_rows:,}")
    
    # Mostrar amostra
    print("\n📊 Amostra dos dados (primeiras 3 linhas):")
    print(df.head(3).to_string())
    
    return True, df.columns.tolist(), total_rows

if __name__ == "__main__":
    print("🔍 VALIDAÇÃO DE ARQUIVOS FONTE")
    print("=" * 60)
    
    # Validar Excel
    excel_ok, excel_cols, excel_rows = validate_excel()
    
    # Validar CNAE
    cnae_ok, cnae_cols, cnae_rows = validate_cnae()
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DA VALIDAÇÃO")
    print("=" * 60)
    
    if excel_ok:
        print(f"✅ Excel: {excel_rows:,} registros, {len(excel_cols)} colunas")
    else:
        print("❌ Excel: FALHOU")
    
    if cnae_ok:
        print(f"✅ CNAE: {cnae_rows:,} registros, {len(cnae_cols)} colunas")
    else:
        print("❌ CNAE: FALHOU")
    
    if excel_ok and cnae_ok:
        print("\n🎉 Todos os arquivos validados com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Validação falhou!")
        sys.exit(1)
