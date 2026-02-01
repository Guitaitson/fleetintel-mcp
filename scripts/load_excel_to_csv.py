#!/usr/bin/env python3
"""
GT-26: Pipeline Excel → CSV
Converte arquivo Excel de emplacamentos para CSV padronizado
"""
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import json
import sys
from datetime import datetime

# Colunas esperadas do Excel (56 colunas)
COLUNAS_ESPERADAS = [
    # Veículo (13 campos)
    "DATA", "CHASSI", "PLACA", "COD_MODELO", "TRACAO", "CILINDRADA",
    "MODELO", "GRUPO MODELO", "MARCA_COMPLETA", "SEGMENTO", "SUBSEGMENTO",
    "ANOFABRICACAO", "ANOMODELO",
    
    # Concessionária (6 campos)
    "CNPJ CONCESSIONARIA", "CONCESSIONARIA", "AREA OPERACIONAL",
    "MUNICIPIO", "ESTADO", "REGIÃO EMPLACAMENTO",
    
    # Preço (2 campos)
    "PRECO", "CONSIDERA",
    
    # Proprietário Básico (9 campos)
    "C_TIPOCNPJPROPRIETARIO", "DOCUMENTO", "NOME PROPRIETÁRIO",
    "DATA ABERTURA EMPRESA", "IDADE EMPRESA", "FAIXA IDADE EMPRESA",
    "SEGMENTO CLIENTE", "PORTE",
    
    # Atividade Econômica (6 campos)
    "CNAE RF", "ATIVIDADE ECONÔMICA", "CNAE AGRUPADO",
    "CO NATUREZA JURIDICA", "NATUREZA JURIDICA", "GRUPO LOCADORA",
    
    # Endereço Proprietário (8 campos)
    "ENDEREÇO PROPRIETÁRIO", "NÚMERO", "COMPLEMENTO", "BAIRRO",
    "CEP", "MUNICÍPIO PROPRIETÁRIO", "C_SG_ESTADO",
    
    # Contatos (14 campos)
    "DDD1", "TEL1", "DDD2", "TEL2", "DDD3", "TEL3",
    "DDD4", "TEL4", "DDD5", "TEL5",
    "DDD CEL1", "CEL1", "DDD CEL2", "CEL2"
]


def validate_columns(df: pd.DataFrame) -> bool:
    """Valida se as colunas esperadas estão presentes"""
    colunas_excel = set(df.columns)
    colunas_esperadas = set(COLUNAS_ESPERADAS)
    
    # Verificar colunas faltando
    faltando = colunas_esperadas - colunas_excel
    if faltando:
        print(f"⚠️  Colunas faltando: {faltando}")
        return False
    
    # Verificar colunas extras
    extras = colunas_excel - colunas_esperadas
    if extras:
        print(f"ℹ️  Colunas extras (serão mantidas): {extras}")
    
    return True


def process_chunk(chunk: pd.DataFrame, chunk_num: int) -> pd.DataFrame:
    """Processa um chunk individual"""
    # Remove linhas completamente vazias
    chunk = chunk.dropna(how='all')
    
    return chunk


def convert_excel_to_csv(
    input_path: str,
    output_path: str,
    chunksize: int = 50000
) -> dict:
    """
    Converte Excel para CSV padronizado
    
    Returns:
        dict: Estatísticas da conversão
    """
    
    print("=" * 60)
    print("📊 GT-26: EXCEL → CSV (V2 - DTYPE CORRETO)")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    # Verificar se arquivo existe
    if not input_file.exists():
        print(f"❌ Arquivo não encontrado: {input_file}")
        return {"error": "Arquivo não encontrado"}
    
    print(f"\n📋 Arquivo de entrada: {input_file}")
    print(f"📊 Tamanho: {input_file.stat().st_size / (1024*1024):.2f} MB")
    
    # CORREÇÃO: Definir dtype para campos de código (NUNCA números!)
    DTYPE_MAP = {
        'DOCUMENTO': str,           # CNPJ/CPF
        'CNPJ CONCESSIONARIA': str, # CNPJ
        'CEP': str,                 # CEP
        'CNAE RF': str,             # CNAE
        'CHASSI': str,              # Chassi
        'PLACA': str,               # Placa
        'CO NATUREZA JURIDICA': str # Código Natureza Jurídica
    }
    
    # Ler primeiras linhas para validar
    print("\n🔍 Validando estrutura...")
    df_sample = pd.read_excel(input_file, nrows=5, dtype=DTYPE_MAP)
    
    if not validate_columns(df_sample):
        return {"error": "Validação de colunas falhou"}
    
    print(f"✅ Estrutura validada: {len(df_sample.columns)} colunas")
    
    # Contar total de linhas
    print("\n🔍 Lendo arquivo completo...")
    df_full = pd.read_excel(input_file, dtype=DTYPE_MAP)
    total_rows = len(df_full)
    print(f"✅ Total de registros: {total_rows:,}")
    
    # Processar e salvar em CSV
    print(f"\n📤 Convertendo para CSV...")
    
    # Criar diretório de saída se não existir
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Processar dados (Excel não suporta chunks, processar tudo de uma vez)
    print(f"   Processando {total_rows:,} registros...")
    df_processed = process_chunk(df_full, 0)
    rows_written = len(df_processed)
    
    # Escrever CSV
    print(f"   Escrevendo CSV...")
    df_processed.to_csv(
        output_file,
        index=False,
        sep=';',
        encoding='utf-8',
        quotechar='"'
    )
    
    chunks_processed = 1
    
    # Validar saída
    print(f"\n✅ Conversão concluída!")
    print(f"   Chunks processados: {chunks_processed}")
    print(f"   Linhas escritas: {rows_written:,}")
    print(f"   Arquivo de saída: {output_file}")
    print(f"   Tamanho: {output_file.stat().st_size / (1024*1024):.2f} MB")
    
    # Retornar estatísticas
    result = {
        "total_rows": total_rows,
        "rows_written": rows_written,
        "chunks_processed": chunks_processed,
        "output_file": str(output_file),
        "validation_passed": True,
        "columns_count": len(df_sample.columns)
    }
    
    return result


if __name__ == "__main__":
    # Configuração
    import sys
    INPUT_PATH = sys.argv[1] if len(sys.argv) > 1 else "data/raw/Emplacamentos teste.xlsx"
    OUTPUT_PATH = "data/processed/emplacamentos_raw.csv"
    
    # Executar conversão
    result = convert_excel_to_csv(
        input_path=INPUT_PATH,
        output_path=OUTPUT_PATH,
        chunksize=50000
    )
    
    # Salvar estatísticas
    stats_file = Path("logs/excel_to_csv_stats.json")
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Estatísticas salvas em: {stats_file}")
    
    # Exibir resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DA CONVERSÃO")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("validation_passed"):
        print("\n🎉 Conversão concluída com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Conversão falhou!")
        sys.exit(1)
