#!/usr/bin/env python3
"""
GT-27: Normalização de Dados
Limpa e normaliza dados para inserção no banco
"""
import pandas as pd
import json
import re
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

def normalize_date(date_str):
    """Normaliza datas para ISO 8601"""
    if pd.isna(date_str) or date_str == '':
        return None
    try:
        return pd.to_datetime(date_str).strftime('%Y-%m-%d')
    except:
        return None

def normalize_cnpj(doc):
    """Normaliza CNPJ para exatamente 14 dígitos com padding"""
    if pd.isna(doc) or doc == '':
        return None
    digits = re.sub(r'\D', '', str(doc))
    if len(digits) == 0:
        return None
    return digits.zfill(14)  # Padding à esquerda com zeros

def normalize_cpf(doc):
    """Normaliza CPF para exatamente 11 dígitos com padding"""
    if pd.isna(doc) or doc == '':
        return None
    digits = re.sub(r'\D', '', str(doc))
    if len(digits) == 0:
        return None
    return digits.zfill(11)  # Padding à esquerda com zeros

def normalize_cep(cep):
    """Normaliza CEP para exatamente 8 dígitos com padding"""
    if pd.isna(cep) or cep == '':
        return None
    digits = re.sub(r'\D', '', str(cep))
    if len(digits) == 0:
        return None
    return digits.zfill(8)  # Padding à esquerda com zeros

def normalize_cnae(cnae):
    """Normaliza CNAE para exatamente 7 dígitos com padding"""
    if pd.isna(cnae) or cnae == '':
        return None
    digits = re.sub(r'\D', '', str(cnae))
    if len(digits) == 0:
        return None
    return digits.zfill(7)  # Padding à esquerda com zeros

def create_contacts_json(row):
    """Cria JSONB de contatos"""
    contacts = {"telefones": [], "celulares": []}
    
    # Telefones
    for i in range(1, 6):
        ddd = row.get(f'DDD{i}')
        tel = row.get(f'TEL{i}')
        if pd.notna(ddd) and pd.notna(tel):
            contacts["telefones"].append(f"{ddd}{tel}")
    
    # Celulares
    for i in range(1, 3):
        ddd = row.get(f'DDD CEL{i}')
        cel = row.get(f'CEL{i}')
        if pd.notna(ddd) and pd.notna(cel):
            contacts["celulares"].append(f"{ddd}{cel}")
    
    return json.dumps(contacts) if (contacts["telefones"] or contacts["celulares"]) else None

def calculate_age_range(idade_dias):
    """Calcula faixa de idade da empresa"""
    if pd.isna(idade_dias):
        return None
    anos = int(idade_dias) / 365
    if anos < 2:
        return "0-2 anos"
    elif anos < 5:
        return "2-5 anos"
    elif anos < 20:
        return "5-20 anos"
    else:
        return "20+ anos"

def normalize_data(input_path: str, output_path: str):
    """Normaliza dados do CSV raw"""
    
    print("=" * 60)
    print("🔧 GT-27: NORMALIZAÇÃO DE DADOS")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Ler CSV raw
    print(f"\n📋 Lendo: {input_path}")
    df = pd.read_csv(input_path, sep=';', encoding='utf-8')
    print(f"✅ {len(df):,} registros lidos")
    
    # Normalizar campos
    print("\n🔧 Normalizando campos...")
    
    # Datas
    df['data_emplacamento'] = df['DATA'].apply(normalize_date)
    df['data_abertura'] = df['DATA ABERTURA EMPRESA'].apply(normalize_date)
    
    # Documentos com padding correto
    df['chassi'] = df['CHASSI']
    df['placa'] = df['PLACA']
    df['cpf_cnpj_proprietario'] = df['DOCUMENTO'].apply(normalize_cnpj)  # CNPJ: 14 dígitos
    df['cnpj_concessionario'] = df['CNPJ CONCESSIONARIA'].apply(normalize_cnpj)  # CNPJ: 14 dígitos
    df['cep'] = df['CEP'].apply(normalize_cep)  # CEP: 8 dígitos
    df['cod_atividade_economica_norm'] = df['CNAE RF'].apply(normalize_cnae)  # CNAE: 7 dígitos
    
    # Contatos em JSONB
    tqdm.pandas(desc="Criando JSONB contatos")
    df['contatos'] = df.progress_apply(create_contacts_json, axis=1)
    
    # Campos calculados
    df['faixa_idade_empresa'] = df['IDADE EMPRESA'].apply(calculate_age_range)
    
    # Mapeamento final de colunas
    column_map = {
        'DATA': 'data_original',
        'CHASSI': 'chassi',
        'PLACA': 'placa',
        'COD_MODELO': 'cod_modelo',
        'TRACAO': 'tracao',
        'CILINDRADA': 'cilindrada',
        'MODELO': 'modelo',
        'GRUPO MODELO': 'grupo_modelo',
        'MARCA_COMPLETA': 'marca',
        'SEGMENTO': 'segmento',
        'SUBSEGMENTO': 'subsegmento',
        'ANOFABRICACAO': 'ano_fabricacao',
        'ANOMODELO': 'ano_modelo',
        'CONCESSIONARIA': 'concessionario',
        'AREA OPERACIONAL': 'area_operacional',
        'MUNICIPIO': 'municipio_emplacamento',
        'ESTADO': 'uf_emplacamento',
        'REGIÃO EMPLACAMENTO': 'regiao_emplacamento',
        'PRECO': 'preco',
        'CONSIDERA': 'preco_validado',
        'C_TIPOCNPJPROPRIETARIO': 'tipo_proprietario',
        'NOME PROPRIETÁRIO': 'nome_proprietario',
        'IDADE EMPRESA': 'idade_empresa',
        'SEGMENTO CLIENTE': 'segmento_cliente',
        'PORTE': 'porte',
        'CNAE RF': 'cod_atividade_economica',
        'ATIVIDADE ECONÔMICA': 'atividade_economica',
        'CNAE AGRUPADO': 'cnae_agrupado',
        'CO NATUREZA JURIDICA': 'codigo_natureza_juridica',
        'NATUREZA JURIDICA': 'natureza_juridica',
        'GRUPO LOCADORA': 'grupo_locadora',
        'ENDEREÇO PROPRIETÁRIO': 'logradouro',
        'NÚMERO': 'numero',
        'COMPLEMENTO': 'complemento',
        'BAIRRO': 'bairro',
        'MUNICÍPIO PROPRIETÁRIO': 'cidade_proprietario',
        'C_SG_ESTADO': 'uf_proprietario'
    }
    
    df_normalized = df.rename(columns=column_map)
    
    # Remover colunas de contato individual (já em JSONB)
    contact_cols = [f'DDD{i}' for i in range(1,6)] + [f'TEL{i}' for i in range(1,6)] + \
                   ['DDD CEL1', 'CEL1', 'DDD CEL2', 'CEL2']
    df_normalized = df_normalized.drop(columns=[c for c in contact_cols if c in df_normalized.columns], errors='ignore')
    
    # Converter strings vazias para None
    df_normalized = df_normalized.replace('', None)
    
    # Garantir que códigos sejam strings (não números)
    string_columns = ['cpf_cnpj_proprietario', 'cnpj_concessionario', 'cep', 
                      'cod_atividade_economica_norm', 'chassi', 'placa']
    for col in string_columns:
        if col in df_normalized.columns:
            df_normalized[col] = df_normalized[col].astype('object')  # Força object dtype
    
    # Salvar CSV normalizado
    print(f"\n📤 Salvando: {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df_normalized.to_csv(output_path, index=False, sep=';', encoding='utf-8')
    
    print(f"✅ {len(df_normalized):,} registros normalizados")
    print(f"✅ {len(df_normalized.columns)} colunas no arquivo final")
    
    return {"rows": len(df_normalized), "columns": len(df_normalized.columns)}

if __name__ == "__main__":
    result = normalize_data(
        "data/processed/emplacamentos_raw.csv",
        "data/processed/emplacamentos_normalized.csv"
    )
    print(f"\n🎉 Normalização concluída: {result}")
