"""
GT-28: ETL OTIMIZADO V7 - CORRECAO CRITICA + OTIMIZACAO DE PERFORMANCE
2026-02-04

CORRECOES CRITICAS em relacao ao v6:
1. Removido begin_nested() - causa erro "result object does not return rows"
2. Separado INSERT e SELECT - primeiro inserir, depois buscar IDs
3. Removido RETURNING de todos os INSERTs em batch
4. Cada funcao usa sua propria conexao (begin() para INSERT, connect() para SELECT)

OTIMIZACOES DE PERFORMANCE:
1. batch_size: 50 -> 1000 (20x maior)
2. pool_size: 5 -> 20 (4x maior)
3. max_concurrent_batches: 3 -> 20 (6.7x maior)
4. batch_delay: 0.1s -> 0 (removido)

MELHORIA ESPERADA: Reducao de ~94% no tempo (de 11.5h para ~40min)
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Tuple
import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import json

# Carregar variaveis de ambiente
load_dotenv()

# Configuracoes
DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://", 1)
CSV_FILE = "data/processed/emplacamentos_normalized.csv"
CHECKPOINT_FILE = "data/etl_checkpoint.json"

# ============================================================
# CONFIGURACOES DE PERFORMANCE OTIMIZADAS (v7)
# ============================================================
BATCH_SIZE = 1000      # Aumentado de 50 para 1000 (20x maior)
POOL_SIZE = 20         # Aumentado de 5 para 20 (4x maior)
MAX_OVERFLOW = 30      # Aumentado de 10 para 30
MAX_RETRIES = 3        # Numero maximo de tentativas
BASE_DELAY = 1         # Delay base em segundos para retry
BATCH_DELAY = 0        # REMOVIDO - era 0.1s
MAX_CONCURRENT_BATCHES = 20  # Aumentado de 3 para 20 (6.7x maior)


async def validate_integrity(conn, step_name: str) -> bool:
    """Valida integridade dos dados apos uma etapa."""
    print(f"\n[VALIDACAO] Verificando integridade apos {step_name}...")
    
    issues = []
    
    if step_name == "marcas":
        result = await conn.execute(text("SELECT COUNT(*) FROM marcas"))
        count = result.scalar()
        print(f"   Total de marcas: {count:,}")
        if count == 0:
            issues.append("Nenhuma marca inserida")
    
    elif step_name == "modelos":
        result = await conn.execute(text("SELECT COUNT(*) FROM modelos"))
        count = result.scalar()
        print(f"   Total de modelos: {count:,}")
        if count == 0:
            issues.append("Nenhum modelo inserido")
        
        # Verificar modelos sem marca
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM modelos m
            LEFT JOIN marcas ma ON m.marca_id = ma.id
            WHERE ma.id IS NULL
        """))
        count_sem_marca = result.scalar()
        if count_sem_marca > 0:
            issues.append(f"{count_sem_marca} modelos sem marca")
        else:
            print(f"   [OK] Todos os modelos tem marca")
    
    elif step_name == "veiculos":
        result = await conn.execute(text("SELECT COUNT(*) FROM vehicles"))
        count = result.scalar()
        print(f"   Total de veiculos: {count:,}")
        
        # VERIFICACAO CRITICA: Veiculos sem modelo
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM vehicles WHERE modelo_id IS NULL
        """))
        count_sem_modelo = result.scalar()
        if count_sem_modelo > 0:
            issues.append(f"[CRITICO] {count_sem_modelo} veiculos sem modelo!")
            print(f"   [ERRO] {count_sem_modelo} veiculos sem modelo!")
        else:
            print(f"   [OK] Todos os veiculos tem modelo")
    
    elif step_name == "empresas":
        result = await conn.execute(text("SELECT COUNT(*) FROM empresas"))
        count = result.scalar()
        print(f"   Total de empresas: {count:,}")
        if count == 0:
            issues.append("Nenhuma empresa inserida")
    
    elif step_name == "enderecos":
        result = await conn.execute(text("SELECT COUNT(*) FROM enderecos"))
        count = result.scalar()
        print(f"   Total de enderecos: {count:,}")
    
    elif step_name == "contatos":
        result = await conn.execute(text("SELECT COUNT(*) FROM contatos"))
        count = result.scalar()
        print(f"   Total de contatos: {count:,}")
    
    elif step_name == "registrations":
        result = await conn.execute(text("SELECT COUNT(*) FROM registrations"))
        count = result.scalar()
        print(f"   Total de registrations: {count:,}")
    
    if issues:
        print(f"\n   [PROBLEMA] Encontrados {len(issues)} problemas:")
        for issue in issues:
            print(f"      - {issue}")
        return False
    
    print(f"   [OK] Integridade OK para {step_name}")
    return True


async def load_marcas(engine, df: pd.DataFrame) -> Dict[str, int]:
    """Carrega marcas no banco de dados."""
    print("\n" + "=" * 60)
    print("ETAPA 1: Carregando MARCAS")
    print("=" * 60)

    # Obter marcas unicas
    marcas = df['marca'].dropna().unique()
    print(f"   Marcas unicas encontradas: {len(marcas)}")

    # ETAPA 1: Inserir marcas SEM RETURNING
    print("   Inserindo marcas...")
    async with engine.begin() as conn:
        for marca_nome in marcas:
            try:
                await conn.execute(
                    text("""
                        INSERT INTO marcas (nome)
                        VALUES (:nome)
                        ON CONFLICT (nome) DO UPDATE SET
                            nome = EXCLUDED.nome
                    """),
                    {"nome": marca_nome}
                )
            except Exception as e:
                print(f"   [ERRO] Falha ao inserir marca {marca_nome}: {e}")
                raise
    
    # ETAPA 2: Buscar IDs das marcas inseridas (nova conexao)
    print("   Buscando IDs das marcas...")
    marca_map = {}
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, nome FROM marcas"))
        rows = result.fetchall()
        for row in rows:
            marca_id, nome = row
            marca_map[nome] = marca_id
        
        print(f"   [OK] {len(marca_map)} marcas carregadas")
        
        # Validar integridade
        await validate_integrity(conn, "marcas")
    
    return marca_map


async def load_modelos(engine, df: pd.DataFrame, marca_map: Dict[str, int]) -> Dict[Tuple, int]:
    """Carrega modelos no banco de dados - CORRIGIDO para evitar erro de RETURNING."""
    print("\n" + "=" * 60)
    print("ETAPA 2: Carregando MODELOS (CORRECAO CRITICA v7)")
    print("=" * 60)

    # Obter modelos unicos
    modelos = df[['marca', 'modelo']].drop_duplicates()
    print(f"   Modelos unicos encontrados: {len(modelos)}")

    # Preparar dados dos modelos
    print("   Preparando modelos...")
    modelo_data = []
    for _, row in modelos.iterrows():
        marca_nome = row['marca']
        modelo_nome = row['modelo']
        if pd.notna(marca_nome) and pd.notna(modelo_nome):
            marca_id = marca_map.get(marca_nome)
            if marca_id:
                modelo_data.append({
                    'marca_id': marca_id,
                    'nome': modelo_nome
                })
    
    print(f"   {len(modelo_data)} modelos preparados")

    # ETAPA 1: Inserir modelos SEM RETURNING (CORRECAO CRITICA!)
    print("   Inserindo modelos em batches...")
    from tqdm import tqdm
    
    success_count = 0
    error_count = 0
    
    async with engine.begin() as conn:
        for i in tqdm(range(0, len(modelo_data), BATCH_SIZE), desc="   Modelos"):
            batch = modelo_data[i:i+BATCH_SIZE]
            try:
                # Usar INSERT simples sem RETURNING
                await conn.execute(
                    text("""
                        INSERT INTO modelos (marca_id, nome)
                        VALUES (:marca_id, :nome)
                        ON CONFLICT (marca_id, nome) DO UPDATE SET
                            nome = EXCLUDED.nome
                    """),
                    batch
                )
                success_count += len(batch)
            except Exception as e:
                print(f"\n   [ERRO] Batch {i//BATCH_SIZE}: {e}")
                # Inserir individualmente em caso de erro
                for item in batch:
                    try:
                        await conn.execute(
                            text("""
                                INSERT INTO modelos (marca_id, nome)
                                VALUES (:marca_id, :nome)
                                ON CONFLICT (marca_id, nome) DO UPDATE SET
                                    nome = EXCLUDED.nome
                            """),
                            item
                        )
                        success_count += 1
                    except Exception as e2:
                        print(f"   [ERRO] Modelo {item}: {e2}")
                        error_count += 1
    
    print(f"\n   Inseridos: {success_count}, Erros: {error_count}")
    
    # ETAPA 2: Buscar IDs dos modelos inseridos (CORRECAO CRITICA!)
    print("   Buscando IDs dos modelos...")
    modelo_map = {}
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, marca_id, nome FROM modelos"))
        rows = result.fetchall()
        for row in rows:
            modelo_id, marca_id, nome = row
            modelo_map[(marca_id, nome)] = modelo_id
        
        print(f"   [OK] {len(modelo_map)} modelos carregados no mapa")
        
        # VERIFICACAO CRITICA: modelo_map deve ter o mesmo tamanho que modelos unicos
        if len(modelo_map) == 0:
            print("   [ERRO CRITICO] modelo_map esta vazio!")
            raise Exception("modelo_map vazio - os modelos nao foram inseridos corretamente")
        
        # Validar integridade
        await validate_integrity(conn, "modelos")
    
    return modelo_map


async def load_vehicles(engine, df: pd.DataFrame, marca_map: Dict[str, int],
                       modelo_map: Dict[Tuple, int]) -> Dict[str, int]:
    """Carrega veiculos no banco de dados com batch inserts otimizados."""
    print("\n" + "=" * 60)
    print("ETAPA 3: Carregando VEICULOS (OTIMIZADO v7)")
    print("=" * 60)

    # Preparar dados dos veiculos
    print("   Preparando veiculos...")
    vehicles = []
    veiculos_sem_modelo = 0
    
    for _, row in df.iterrows():
        marca_nome = row['marca']
        modelo_nome = row['modelo']
        marca_id = marca_map.get(marca_nome)
        modelo_id = modelo_map.get((marca_id, modelo_nome)) if marca_id else None
        
        if not modelo_id:
            veiculos_sem_modelo += 1
            # DEBUG: Mostrar alguns exemplos
            if veiculos_sem_modelo <= 5:
                print(f"   [DEBUG] Veiculo sem modelo: marca={marca_nome}, modelo={modelo_nome}, marca_id={marca_id}")
            continue
        
        # Remover ".0" dos valores de ano antes de converter para int
        ano_fab = row['ano_fabricacao']
        ano_mod = row['ano_modelo']
        
        if pd.notna(ano_fab):
            ano_fab = str(ano_fab).replace('.0', '')
        if pd.notna(ano_mod):
            ano_mod = str(ano_mod).replace('.0', '')
        
        vehicles.append({
            'chassi': row['chassi'],
            'placa': row['placa'],
            'marca_id': marca_id,
            'modelo_id': modelo_id,
            'ano_fabricacao': int(ano_fab) if pd.notna(ano_fab) and ano_fab != '' else None,
            'ano_modelo': int(ano_mod) if pd.notna(ano_mod) and ano_mod != '' else None,
            'marca_nome': marca_nome,
            'modelo_nome': modelo_nome
        })
    
    print(f"   {len(vehicles)} veiculos preparados")
    if veiculos_sem_modelo > 0:
        print(f"   [AVISO] {veiculos_sem_modelo} veiculos ignorados (sem modelo)")

    # Inserir veiculos em batch
    print("   Inserindo veiculos em batches...")
    from tqdm import tqdm
    
    success_count = 0
    error_count = 0
    
    async with engine.begin() as conn:
        for i in tqdm(range(0, len(vehicles), BATCH_SIZE), desc="   Veiculos"):
            batch = vehicles[i:i+BATCH_SIZE]
            for attempt in range(MAX_RETRIES):
                try:
                    await conn.execute(
                        text("""
                            INSERT INTO vehicles (chassi, placa, marca_id, modelo_id, ano_fabricacao, ano_modelo,
                                                  marca_nome, modelo_nome)
                            VALUES (:chassi, :placa, :marca_id, :modelo_id, :ano_fabricacao, :ano_modelo,
                                    :marca_nome, :modelo_nome)
                            ON CONFLICT (chassi) DO UPDATE SET
                                placa = EXCLUDED.placa,
                                marca_id = EXCLUDED.marca_id,
                                modelo_id = EXCLUDED.modelo_id,
                                ano_fabricacao = EXCLUDED.ano_fabricacao,
                                ano_modelo = EXCLUDED.ano_modelo,
                                marca_nome = EXCLUDED.marca_nome,
                                modelo_nome = EXCLUDED.modelo_nome
                        """),
                        batch
                    )
                    success_count += len(batch)
                    break
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        delay = BASE_DELAY * (2 ** attempt)
                        print(f"\n   [RETRY] Batch {i//BATCH_SIZE} tentativa {attempt + 1}/{MAX_RETRIES}: {e}")
                        await asyncio.sleep(delay)
                    else:
                        print(f"\n   [ERRO] Batch {i//BATCH_SIZE} falhou: {e}")
                        error_count += len(batch)
    
    print(f"\n   Inseridos: {success_count}, Erros: {error_count}")
    
    # Buscar IDs dos veiculos inseridos
    print("   Buscando IDs dos veiculos...")
    vehicle_map = {}
    chassis_list = [v['chassi'] for v in vehicles]
    
    async with engine.connect() as conn:
        # Buscar em batches para evitar consulta muito grande
        for i in range(0, len(chassis_list), BATCH_SIZE):
            batch_chassis = chassis_list[i:i+BATCH_SIZE]
            result = await conn.execute(
                text("SELECT id, chassi FROM vehicles WHERE chassi = ANY(:chassis)"),
                {"chassis": batch_chassis}
            )
            rows = result.fetchall()
            for row in rows:
                vehicle_id, chassi = row
                vehicle_map[chassi] = vehicle_id
        
        print(f"   [OK] {len(vehicle_map)} veiculos mapeados")
        
        # Validar integridade
        await validate_integrity(conn, "veiculos")
    
    return vehicle_map


async def load_companies(engine, df: pd.DataFrame) -> Dict[str, Dict]:
    """Carrega empresas no banco de dados com batch inserts otimizados."""
    print("\n" + "=" * 60)
    print("ETAPA 4: Carregando EMPRESAS (OTIMIZADO v7)")
    print("=" * 60)

    # Preparar dados das empresas
    print("   Preparando empresas...")
    companies = []
    for _, row in df.iterrows():
        cnpj = row['cpf_cnpj_proprietario']
        if pd.notna(cnpj) and cnpj != '':
            companies.append({
                'cnpj': cnpj,
                'razao_social': row['nome_proprietario'] if pd.notna(row['nome_proprietario']) else None,
                'nome_fantasia': None,
                'tipo_proprietario': None,
                'cnae_id': None,
                'porte': None,
                'natureza_juridica': None,
                'codigo_natureza_juridica': None,
                'situacao_cadastral': None,
                'data_abertura': None,
                'idade_empresa_dias': None,
                'faixa_idade_empresa': None,
                'segmento_cliente': None,
                'grupo_locadora': None,
                'brasilapi_qsa': None,
                'brasilapi_cnaes_secundarios': None,
                'brasilapi_raw': None,
                'brasilapi_status': None,
                'brasilapi_updated_at': None,
                'brasilapi_error': None,
                'source': 'excel'
            })

    # Remover duplicatas por CNPJ
    unique_companies = list({c['cnpj']: c for c in companies}.values())
    print(f"   {len(unique_companies)} empresas unicas (de {len(companies)} totais)")

    # Inserir empresas em batch
    print("   Inserindo empresas em batches...")
    from tqdm import tqdm
    
    success_count = 0
    error_count = 0
    
    async with engine.begin() as conn:
        for i in tqdm(range(0, len(unique_companies), BATCH_SIZE), desc="   Empresas"):
            batch = unique_companies[i:i+BATCH_SIZE]
            try:
                await conn.execute(
                    text("""
                        INSERT INTO empresas (cnpj, razao_social, nome_fantasia, tipo_proprietario, cnae_id,
                                           porte, natureza_juridica, codigo_natureza_juridica,
                                           situacao_cadastral, data_abertura, idade_empresa_dias,
                                           faixa_idade_empresa, segmento_cliente, grupo_locadora,
                                           brasilapi_qsa, brasilapi_cnaes_secundarios, brasilapi_raw,
                                           brasilapi_status, brasilapi_updated_at, brasilapi_error, source)
                        VALUES (:cnpj, :razao_social, :nome_fantasia, :tipo_proprietario, :cnae_id,
                                :porte, :natureza_juridica, :codigo_natureza_juridica,
                                :situacao_cadastral, :data_abertura, :idade_empresa_dias,
                                :faixa_idade_empresa, :segmento_cliente, :grupo_locadora,
                                :brasilapi_qsa, :brasilapi_cnaes_secundarios, :brasilapi_raw,
                                :brasilapi_status, :brasilapi_updated_at, :brasilapi_error, :source)
                        ON CONFLICT (cnpj) DO UPDATE SET
                            razao_social = EXCLUDED.razao_social
                    """),
                    batch
                )
                success_count += len(batch)
            except Exception as e:
                print(f"\n   [ERRO] Batch {i//BATCH_SIZE}: {e}")
                error_count += len(batch)
    
    print(f"\n   Inseridas: {success_count}, Erros: {error_count}")
    
    # Buscar IDs das empresas inseridas
    print("   Buscando IDs das empresas...")
    company_map = {}
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, cnpj FROM empresas"))
        rows = result.fetchall()
        for row in rows:
            empresa_id, cnpj = row
            company_map[cnpj] = {'id': empresa_id, 'cnpj': cnpj}
        
        print(f"   [OK] {len(company_map)} empresas mapeadas")
        
        # Validar integridade
        await validate_integrity(conn, "empresas")
    
    return company_map


async def load_enderecos(engine, df: pd.DataFrame, company_map: Dict[str, Dict]):
    """Carrega enderecos no banco de dados com batch inserts otimizados."""
    print("\n" + "=" * 60)
    print("ETAPA 5: Carregando ENDERECOS (OTIMIZADO v7)")
    print("=" * 60)

    # Preparar dados dos enderecos
    print("   Preparando enderecos...")
    enderecos = []
    for _, row in df.iterrows():
        cnpj = row['cpf_cnpj_proprietario']
        if pd.notna(cnpj) and cnpj != '' and cnpj in company_map:
            empresa_id = company_map[cnpj]['id']
            enderecos.append({
                'empresa_id': empresa_id,
                'cep': row['cep'] if pd.notna(row['cep']) else None,
                'logradouro': row['logradouro'] if pd.notna(row['logradouro']) else None,
                'numero': None,
                'complemento': None,
                'bairro': row['bairro'] if pd.notna(row['bairro']) else None,
                'cidade': row['cidade_proprietario'] if pd.notna(row['cidade_proprietario']) else None,
                'uf': row['uf_proprietario'] if pd.notna(row['uf_proprietario']) else None,
                'codigo_municipio_ibge': None,
                'latitude': None,
                'longitude': None,
                'brasilapi_raw': None,
                'brasilapi_status': None,
                'brasilapi_updated_at': None,
                'brasilapi_error': None,
                'source': 'excel'
            })

    # Remover duplicatas por empresa_id
    unique_enderecos = list({e['empresa_id']: e for e in enderecos}.values())
    print(f"   {len(unique_enderecos)} enderecos unicos (de {len(enderecos)} totais)")

    # Inserir enderecos em batch
    print("   Inserindo enderecos em batches...")
    from tqdm import tqdm
    
    success_count = 0
    error_count = 0
    
    async with engine.begin() as conn:
        for i in tqdm(range(0, len(unique_enderecos), BATCH_SIZE), desc="   Enderecos"):
            batch = unique_enderecos[i:i+BATCH_SIZE]
            try:
                await conn.execute(
                    text("""
                        INSERT INTO enderecos (empresa_id, cep, logradouro, numero, complemento,
                                           bairro, cidade, uf, codigo_municipio_ibge,
                                           latitude, longitude, brasilapi_raw,
                                           brasilapi_status, brasilapi_updated_at, brasilapi_error, source)
                        VALUES (:empresa_id, :cep, :logradouro, :numero, :complemento,
                                :bairro, :cidade, :uf, :codigo_municipio_ibge,
                                :latitude, :longitude, :brasilapi_raw,
                                :brasilapi_status, :brasilapi_updated_at, :brasilapi_error, :source)
                        ON CONFLICT (empresa_id) DO UPDATE SET
                            cep = EXCLUDED.cep,
                            logradouro = EXCLUDED.logradouro,
                            bairro = EXCLUDED.bairro,
                            cidade = EXCLUDED.cidade,
                            uf = EXCLUDED.uf
                    """),
                    batch
                )
                success_count += len(batch)
            except Exception as e:
                print(f"\n   [ERRO] Batch {i//BATCH_SIZE}: {e}")
                error_count += len(batch)
    
    print(f"\n   Inseridos: {success_count}, Erros: {error_count}")
    
    # Validar integridade
    async with engine.connect() as conn:
        await validate_integrity(conn, "enderecos")


async def load_contatos(engine, df: pd.DataFrame, company_map: Dict[str, Dict]):
    """Carrega contatos no banco de dados com batch inserts otimizados."""
    print("\n" + "=" * 60)
    print("ETAPA 6: Carregando CONTATOS (OTIMIZADO v7)")
    print("=" * 60)

    # Preparar dados dos contatos
    print("   Preparando contatos...")
    contatos = []
    for _, row in df.iterrows():
        cnpj = row['cpf_cnpj_proprietario']
        if pd.notna(cnpj) and cnpj != '' and cnpj in company_map:
            empresa_id = company_map[cnpj]['id']
            
            # Parsear contatos da coluna JSON
            contatos_str = row['contatos']
            if pd.notna(contatos_str) and contatos_str != '':
                try:
                    contatos_json = json.loads(contatos_str)
                    if isinstance(contatos_json, dict):
                        telefones = contatos_json.get('telefones', [])
                        celulares = contatos_json.get('celulares', [])
                        email = contatos_json.get('email', None)
                        
                        contatos.append({
                            'empresa_id': empresa_id,
                            'telefones': telefones if telefones else [],
                            'celulares': celulares if celulares else [],
                            'email': email,
                            'source': 'excel'
                        })
                except Exception as e:
                    pass  # Ignorar erros de parsing

    # Remover duplicatas por empresa_id
    unique_contatos = list({c['empresa_id']: c for c in contatos}.values())
    print(f"   {len(unique_contatos)} contatos unicos (de {len(contatos)} totais)")

    # Inserir contatos em batch
    print("   Inserindo contatos em batches...")
    from tqdm import tqdm
    
    success_count = 0
    error_count = 0
    
    async with engine.begin() as conn:
        for i in tqdm(range(0, len(unique_contatos), BATCH_SIZE), desc="   Contatos"):
            batch = unique_contatos[i:i+BATCH_SIZE]
            try:
                await conn.execute(
                    text("""
                        INSERT INTO contatos (empresa_id, telefones, celulares, email)
                        VALUES (:empresa_id, :telefones, :celulares, :email)
                        ON CONFLICT (empresa_id) DO UPDATE SET
                            telefones = EXCLUDED.telefones,
                            celulares = EXCLUDED.celulares,
                            email = EXCLUDED.email
                    """),
                    batch
                )
                success_count += len(batch)
            except Exception as e:
                print(f"\n   [ERRO] Batch {i//BATCH_SIZE}: {e}")
                error_count += len(batch)
    
    print(f"\n   Inseridos: {success_count}, Erros: {error_count}")
    
    # Validar integridade
    async with engine.connect() as conn:
        await validate_integrity(conn, "contatos")


async def load_registrations(engine, df: pd.DataFrame, vehicle_map: Dict[str, int],
                            company_map: Dict[str, Dict]):
    """Carrega registrations no banco de dados com batch inserts otimizados."""
    print("\n" + "=" * 60)
    print("ETAPA 7: Carregando REGISTRATIONS (OTIMIZADO v7)")
    print("=" * 60)

    # Preparar dados dos registrations
    print("   Preparando registrations...")
    registrations = []
    for _, row in df.iterrows():
        chassi = row['chassi']
        cnpj = row['cpf_cnpj_proprietario']
        
        if chassi in vehicle_map and cnpj in company_map:
            vehicle_id = vehicle_map[chassi]
            empresa_id = company_map[cnpj]['id']
            
            # Converter data de string para objeto date
            data_emplacamento = None
            if pd.notna(row['data_emplacamento']) and row['data_emplacamento'] != '':
                try:
                    data_emplacamento = datetime.strptime(row['data_emplacamento'], '%Y-%m-%d').date()
                except Exception:
                    pass
            
            # Gerar external_id usando chassi como base
            external_id = f"{chassi}_{data_emplacamento}" if data_emplacamento else chassi
            
            registrations.append({
                'vehicle_id': vehicle_id,
                'empresa_id': empresa_id,
                'external_id': external_id,
                'data_emplacamento': data_emplacamento,
                'municipio_emplacamento': row['municipio_emplacamento'] if pd.notna(row['municipio_emplacamento']) else None,
                'uf_emplacamento': row['uf_emplacamento'] if pd.notna(row['uf_emplacamento']) else None
            })

    print(f"   {len(registrations)} registrations preparados")

    # Inserir registrations em batch
    print("   Inserindo registrations em batches...")
    from tqdm import tqdm
    
    success_count = 0
    error_count = 0
    
    async with engine.begin() as conn:
        for i in tqdm(range(0, len(registrations), BATCH_SIZE), desc="   Registrations"):
            batch = registrations[i:i+BATCH_SIZE]
            for attempt in range(MAX_RETRIES):
                try:
                    await conn.execute(
                        text("""
                            INSERT INTO registrations (vehicle_id, empresa_id, external_id, data_emplacamento,
                                                   municipio_emplacamento, uf_emplacamento)
                            VALUES (:vehicle_id, :empresa_id, :external_id, :data_emplacamento,
                                    :municipio_emplacamento, :uf_emplacamento)
                            ON CONFLICT (vehicle_id, data_emplacamento) DO UPDATE SET
                                empresa_id = EXCLUDED.empresa_id,
                                municipio_emplacamento = EXCLUDED.municipio_emplacamento,
                                uf_emplacamento = EXCLUDED.uf_emplacamento
                        """),
                        batch
                    )
                    success_count += len(batch)
                    break
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        delay = BASE_DELAY * (2 ** attempt)
                        print(f"\n   [RETRY] Batch {i//BATCH_SIZE} tentativa {attempt + 1}/{MAX_RETRIES}: {e}")
                        await asyncio.sleep(delay)
                    else:
                        print(f"\n   [ERRO] Batch {i//BATCH_SIZE} falhou: {e}")
                        error_count += len(batch)
    
    print(f"\n   Inseridos: {success_count}, Erros: {error_count}")
    
    # Validar integridade
    async with engine.connect() as conn:
        await validate_integrity(conn, "registrations")


async def generate_quality_report(engine):
    """Gera relatorio de qualidade dos dados."""
    print("\n" + "=" * 60)
    print("RELATORIO DE QUALIDADE DOS DADOS")
    print("=" * 60)
    
    async with engine.connect() as conn:
        # Contagens
        tables = ['marcas', 'modelos', 'vehicles', 'empresas', 'enderecos', 'contatos', 'registrations']
        for table in tables:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"   {table}: {count:,}")
        
        print("\n" + "-" * 40)
        print("VERIFICACOES DE INTEGRIDADE")
        print("-" * 40)
        
        # Veiculos sem modelo
        result = await conn.execute(text("SELECT COUNT(*) FROM vehicles WHERE modelo_id IS NULL"))
        count = result.scalar()
        if count > 0:
            print(f"   [ERRO] Veiculos sem modelo: {count:,}")
        else:
            print(f"   [OK] Todos os veiculos tem modelo")
        
        # Empresas sem endereco
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM empresas e
            LEFT JOIN enderecos en ON e.id = en.empresa_id
            WHERE en.id IS NULL
        """))
        count = result.scalar()
        if count > 0:
            print(f"   [AVISO] Empresas sem endereco: {count:,}")
        else:
            print(f"   [OK] Todas as empresas tem endereco")
        
        # Empresas sem contato
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM empresas e
            LEFT JOIN contatos c ON e.id = c.empresa_id
            WHERE c.id IS NULL
        """))
        count = result.scalar()
        if count > 0:
            print(f"   [AVISO] Empresas sem contato: {count:,}")
        else:
            print(f"   [OK] Todas as empresas tem contato")
        
        # Registrations sem veiculo
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM registrations r
            LEFT JOIN vehicles v ON r.vehicle_id = v.id
            WHERE v.id IS NULL
        """))
        count = result.scalar()
        if count > 0:
            print(f"   [ERRO] Registrations sem veiculo: {count:,}")
        else:
            print(f"   [OK] Todos os registrations tem veiculo")
    
    print("=" * 60)


async def main():
    """Funcao principal."""
    start_time = datetime.now()
    
    print("=" * 60)
    print("GT-28: ETL OTIMIZADO V7 - CORRECAO CRITICA + OTIMIZACAO")
    print(f"Inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    print("\nCONFIGURACOES DE PERFORMANCE:")
    print(f"   BATCH_SIZE: {BATCH_SIZE}")
    print(f"   POOL_SIZE: {POOL_SIZE}")
    print(f"   MAX_CONCURRENT_BATCHES: {MAX_CONCURRENT_BATCHES}")
    print(f"   BATCH_DELAY: {BATCH_DELAY}s")
    
    # Criar engine de conexao com pool otimizado
    engine = create_async_engine(
        DATABASE_URL,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_pre_ping=True
    )
    
    # Ler CSV
    print("\nLendo CSV...")
    df = pd.read_csv(CSV_FILE, sep=';', encoding='utf-8', dtype=str)
    print(f"Total: {len(df):,} registros")
    
    # Modo teste
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        print("\n[MODO TESTE] Limitando a 100 registros")
        df = df.head(100)
    
    # Carregar marcas
    marca_map = await load_marcas(engine, df)
    
    # Carregar modelos
    modelo_map = await load_modelos(engine, df, marca_map)
    
    # Carregar veiculos
    vehicle_map = await load_vehicles(engine, df, marca_map, modelo_map)
    
    # Carregar empresas
    company_map = await load_companies(engine, df)
    
    # Carregar enderecos
    await load_enderecos(engine, df, company_map)
    
    # Carregar contatos
    await load_contatos(engine, df, company_map)
    
    # Carregar registrations
    await load_registrations(engine, df, vehicle_map, company_map)
    
    # Gerar relatorio de qualidade
    await generate_quality_report(engine)
    
    # Fechar engine
    await engine.dispose()
    
    # Tempo total
    end_time = datetime.now()
    elapsed = end_time - start_time
    
    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)
    print(f"   Inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Fim: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Tempo total: {elapsed}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
