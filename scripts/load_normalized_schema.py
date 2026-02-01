#!/usr/bin/env python3
"""
GT-28: ETL Otimizado para Schema Normalizado
Target: <1 hora para 974k registros (270+ reg/s)
"""
import asyncio
import pandas as pd
import sys
import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from tqdm import tqdm

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://", 1)
engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    pool_size=5, 
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600
)

def generate_external_id(chassi: str, data: str) -> str:
    """Gera external_id único e determinístico"""
    if not chassi or not data:
        import uuid
        return str(uuid.uuid4())
    ext_id = f"{chassi}_{data}"
    return hashlib.md5(ext_id.encode()).hexdigest() if len(ext_id) > 50 else ext_id

async def load_marcas_modelos(conn, df):
    """Etapa 1: Carregar marcas e modelos"""
    print("\n📦 Etapa 1: Carregando marcas e modelos...")
    
    # Extrair marcas únicas
    marcas_unicas = df['marca'].dropna().unique()
    print(f"   Marcas únicas: {len(marcas_unicas)}")
    
    for marca in tqdm(marcas_unicas, desc="Inserindo marcas"):
        await conn.execute(
            text("INSERT INTO marcas (nome) VALUES (:nome) ON CONFLICT (nome) DO NOTHING"),
            {"nome": marca}
        )
    
    # Buscar IDs das marcas
    result = await conn.execute(text("SELECT id, nome FROM marcas"))
    marca_map = {row[1]: row[0] for row in result}
    
    # Extrair modelos únicos (com marca)
    modelos_df = df[['marca', 'modelo', 'cod_modelo', 'segmento', 'subsegmento', 
                      'grupo_modelo', 'tracao', 'cilindrada']].drop_duplicates()
    
    print(f"   Modelos únicos: {len(modelos_df)}")
    
    for _, row in tqdm(modelos_df.iterrows(), total=len(modelos_df), desc="Inserindo modelos"):
        if pd.notna(row['marca']) and pd.notna(row['modelo']):
            try:
                await conn.execute(
                    text("""
                        INSERT INTO modelos (marca_id, nome, cod_modelo, segmento, subsegmento, 
                                            grupo_modelo, tracao, cilindrada)
                        VALUES (:marca_id, :nome, :cod_modelo, :segmento, :subsegmento,
                                :grupo_modelo, :tracao, :cilindrada)
                        ON CONFLICT (marca_id, nome) DO NOTHING
                    """),
                    {
                        "marca_id": marca_map.get(row['marca']),
                        "nome": row['modelo'],
                        "cod_modelo": row.get('cod_modelo'),
                        "segmento": row.get('segmento'),
                        "subsegmento": row.get('subsegmento'),
                        "grupo_modelo": row.get('grupo_modelo'),
                        "tracao": row.get('tracao'),
                        "cilindrada": row.get('cilindrada')
                    }
                )
            except Exception as e:
                continue
    
    # Buscar IDs dos modelos
    result = await conn.execute(text("""
        SELECT m.id, ma.nome as marca, m.nome as modelo
        FROM modelos m
        JOIN marcas ma ON m.marca_id = ma.id
    """))
    modelo_map = {(row[1], row[2]): row[0] for row in result}
    
    return marca_map, modelo_map

async def load_vehicles(conn, df, marca_map, modelo_map):
    """Etapa 2: Carregar vehicles"""
    print("\n🚗 Etapa 2: Carregando veículos...")
    
    vehicles_df = df[['chassi', 'placa', 'marca', 'modelo', 'ano_fabricacao', 'ano_modelo']].drop_duplicates(subset=['chassi'])
    
    vehicle_map = {}
    
    for _, row in tqdm(vehicles_df.iterrows(), total=len(vehicles_df), desc="Inserindo vehicles"):
        if pd.notna(row['chassi']):
            marca_id = marca_map.get(row['marca']) if pd.notna(row['marca']) else None
            modelo_id = modelo_map.get((row['marca'], row['modelo'])) if pd.notna(row['marca']) and pd.notna(row['modelo']) else None
            
            result = await conn.execute(
                text("""
                    INSERT INTO vehicles (chassi, placa, marca_id, modelo_id, ano_fabricacao, ano_modelo,
                                         marca_nome, modelo_nome)
                    VALUES (:chassi, :placa, :marca_id, :modelo_id, :ano_fabricacao, :ano_modelo,
                            :marca_nome, :modelo_nome)
                    ON CONFLICT (chassi) DO UPDATE SET
                        placa = EXCLUDED.placa,
                        updated_at = NOW()
                    RETURNING id
                """),
                {
                    "chassi": row['chassi'],
                    "placa": row.get('placa'),
                    "marca_id": marca_id,
                    "modelo_id": modelo_id,
                    "ano_fabricacao": int(row['ano_fabricacao']) if pd.notna(row['ano_fabricacao']) else None,
                    "ano_modelo": int(row['ano_modelo']) if pd.notna(row['ano_modelo']) else None,
                    "marca_nome": row.get('marca'),
                    "modelo_nome": row.get('modelo')
                }
            )
            vehicle_id = result.scalar()
            vehicle_map[row['chassi']] = vehicle_id
    
    return vehicle_map

async def load_empresas_enderecos_contatos(conn, df):
    """Etapa 3: Carregar empresas, endereços e contatos"""
    print("\n🏢 Etapa 3: Carregando empresas, endereços e contatos...")
    
    # Agrupar por CNPJ
    empresas_df = df.groupby('cpf_cnpj_proprietario').first().reset_index()
    empresas_df = empresas_df[empresas_df['cpf_cnpj_proprietario'].notna()]
    
    empresa_map = {}
    
    for _, row in tqdm(empresas_df.iterrows(), total=len(empresas_df), desc="Inserindo empresas"):
        # CNPJ já vem normalizado como string de 14 dígitos
        cnpj = row['cpf_cnpj_proprietario']
        if pd.isna(cnpj) or not cnpj:
            continue
        
        # Inserir empresa
        result = await conn.execute(
            text("""
                INSERT INTO empresas (cnpj, razao_social, nome_fantasia, tipo_proprietario,
                                     porte, situacao_cadastral, data_abertura,
                                     segmento_cliente, grupo_locadora, source)
                VALUES (:cnpj, :razao_social, :nome_fantasia, :tipo_proprietario,
                        :porte, :situacao_cadastral, :data_abertura,
                        :segmento_cliente, :grupo_locadora, 'excel')
                ON CONFLICT (cnpj) DO UPDATE SET
                    razao_social = COALESCE(EXCLUDED.razao_social, empresas.razao_social),
                    updated_at = NOW()
                RETURNING id
            """),
            {
                "cnpj": cnpj,  # CNPJ já normalizado (14 dígitos)
                "razao_social": row.get('nome_proprietario'),
                "nome_fantasia": None,
                "tipo_proprietario": row.get('tipo_proprietario'),
                "porte": row.get('porte'),
                "situacao_cadastral": None,
                "data_abertura": pd.to_datetime(row.get('data_abertura')).date() if pd.notna(row.get('data_abertura')) else None,
                "segmento_cliente": row.get('segmento_cliente'),
                "grupo_locadora": row.get('grupo_locadora')
            }
        )
        empresa_id = result.scalar()
        # Salvar no map usando CNPJ como chave (string de 14 dígitos)
        empresa_map[cnpj] = empresa_id
        
        # Inserir endereço (CEP já vem normalizado com 8 dígitos)
        if pd.notna(row.get('cep')) or pd.notna(row.get('cidade_proprietario')):
            await conn.execute(
                text("""
                    INSERT INTO enderecos (empresa_id, cep, logradouro, numero, complemento,
                                          bairro, cidade, uf, source)
                    VALUES (:empresa_id, :cep, :logradouro, :numero, :complemento,
                            :bairro, :cidade, :uf, 'excel')
                    ON CONFLICT (empresa_id) DO NOTHING
                """),
                {
                    "empresa_id": empresa_id,
                    "cep": row.get('cep'),  # CEP já normalizado (8 dígitos)
                    "logradouro": row.get('logradouro'),
                    "numero": row.get('numero'),
                    "complemento": row.get('complemento'),
                    "bairro": row.get('bairro'),
                    "cidade": row.get('cidade_proprietario'),
                    "uf": row.get('uf_proprietario')
                }
            )
        
        # Inserir contatos
        if pd.notna(row.get('contatos')):
            try:
                import json
                contatos_json = json.loads(row['contatos']) if isinstance(row['contatos'], str) else row['contatos']
                
                await conn.execute(
                    text("""
                        INSERT INTO contatos (empresa_id, telefones, celulares)
                        VALUES (:empresa_id, :telefones, :celulares)
                        ON CONFLICT (empresa_id) DO NOTHING
                    """),
                    {
                        "empresa_id": empresa_id,
                        "telefones": contatos_json.get('telefones', []),
                        "celulares": contatos_json.get('celulares', [])
                    }
                )
            except:
                pass
    
    return empresa_map

async def load_registrations(conn, df, vehicle_map, empresa_map):
    """Etapa 4: Carregar registrations"""
    print("\n📋 Etapa 4: Carregando registrations...")
    
    success_count = 0
    error_count = 0
    
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Inserindo registrations"):
        try:
            vehicle_id = vehicle_map.get(row['chassi'])
            # CNPJ já vem normalizado (string de 14 dígitos)
            cnpj_key = row['cpf_cnpj_proprietario'] if pd.notna(row['cpf_cnpj_proprietario']) else None
            empresa_id = empresa_map.get(cnpj_key) if cnpj_key else None
            
            if not vehicle_id or not empresa_id:
                error_count += 1
                continue
            
            # Converter data
            data_emplac = None
            if pd.notna(row.get('data_emplacamento')):
                try:
                    data_emplac = pd.to_datetime(row['data_emplacamento']).date()
                except:
                    pass
            
            if not data_emplac:
                error_count += 1
                continue
            
            # Gerar external_id
            external_id = generate_external_id(row['chassi'], str(data_emplac))
            
            await conn.execute(
                text("""
                    INSERT INTO registrations (external_id, vehicle_id, empresa_id,
                                              data_emplacamento, municipio_emplacamento,
                                              uf_emplacamento, regiao_emplacamento,
                                              cnpj_concessionario, concessionario,
                                              area_operacional, preco, preco_validado,
                                              fonte, versao_carga)
                    VALUES (:external_id, :vehicle_id, :empresa_id,
                            :data_emplacamento, :municipio_emplacamento,
                            :uf_emplacamento, :regiao_emplacamento,
                            :cnpj_concessionario, :concessionario,
                            :area_operacional, :preco, :preco_validado,
                            'excel_inicial', 1)
                    ON CONFLICT (external_id) DO NOTHING
                """),
                {
                    "external_id": external_id,
                    "vehicle_id": vehicle_id,
                    "empresa_id": empresa_id,
                    "data_emplacamento": data_emplac,
                    "municipio_emplacamento": row.get('municipio_emplacamento'),
                    "uf_emplacamento": row.get('uf_emplacamento'),
                    "regiao_emplacamento": row.get('regiao_emplacamento'),
                    "cnpj_concessionario": row.get('cnpj_concessionario'),  # CNPJ já normalizado
                    "concessionario": row.get('concessionario'),
                    "area_operacional": row.get('area_operacional'),
                    "preco": float(row['preco']) if pd.notna(row.get('preco')) else None,
                    "preco_validado": row.get('preco_validado')
                }
            )
            success_count += 1
            
        except Exception as e:
            error_count += 1
            continue
    
    return success_count, error_count

async def load_data(input_path: str, test_mode: bool = False):
    """Função principal de carga"""
    print("=" * 60)
    print("🚀 GT-28: ETL OTIMIZADO - SCHEMA NORMALIZADO")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Definir dtypes para garantir que códigos sejam lidos como strings
    DTYPE_MAP = {
        'cpf_cnpj_proprietario': str,
        'cnpj_concessionario': str,
        'cep': str,
        'cod_atividade_economica_norm': str,
        'chassi': str,
        'placa': str
    }
    
    # Ler CSV
    print(f"\n📋 Lendo CSV...")
    if test_mode:
        df = pd.read_csv(input_path, sep=';', encoding='utf-8', nrows=100, dtype=DTYPE_MAP)
        print(f"🧪 MODO TESTE: {len(df):,} registros")
    else:
        df = pd.read_csv(input_path, sep=';', encoding='utf-8', low_memory=False, dtype=DTYPE_MAP)
        print(f"📊 Total: {len(df):,} registros")
    
    start_time = datetime.now()
    
    async with engine.begin() as conn:
        # Etapa 1
        marca_map, modelo_map = await load_marcas_modelos(conn, df)
        
        # Etapa 2
        vehicle_map = await load_vehicles(conn, df, marca_map, modelo_map)
        
        # Etapa 3
        empresa_map = await load_empresas_enderecos_contatos(conn, df)
        
        # Etapa 4
        success_count, error_count = await load_registrations(conn, df, vehicle_map, empresa_map)
    
    duration = (datetime.now() - start_time).total_seconds()
    
    print(f"\n" + "=" * 60)
    print(f"✅ Registrations inseridos: {success_count:,}")
    print(f"⚠️  Erros: {error_count:,}")
    print(f"⏱️  Tempo: {int(duration/60)}min {int(duration%60)}s")
    print(f"📊 Taxa: {int(success_count/duration)} reg/s")
    print("=" * 60)
    
    return {"success": success_count, "errors": error_count, "duration": duration}

if __name__ == "__main__":
    test_mode = "--full" not in sys.argv
    
    if test_mode:
        print("\n🧪 Executando em MODO TESTE (10.000 registros)")
        print("   Use --full para carga completa\n")
    
    result = asyncio.run(load_data(
        "data/processed/emplacamentos_normalized.csv",
        test_mode=test_mode
    ))
    
    print(f"\n📊 Resultado final: {result}")
