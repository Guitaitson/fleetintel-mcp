"""
Script para verificar tipos de dados no banco de dados Supabase
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco
DB_HOST = os.getenv('SUPABASE_DB_HOST')
DB_PORT = os.getenv('SUPABASE_DB_PORT', '5432')
DB_NAME = os.getenv('SUPABASE_DB_NAME')
DB_USER = os.getenv('SUPABASE_DB_USER')
DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD')

async def check_data_types():
    """Verificar tipos de dados no banco de dados"""
    
    print("=" * 80)
    print("VERIFICANDO TIPOS DE DADOS NO BANCO DE DADOS")
    print("=" * 80)
    
    # Conectar ao banco
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    
    try:
        # Verificar tipos de colunas críticas
        print("\n[INFO] Verificando tipos de colunas críticas...")
        
        critical_columns = [
            ('empresas', 'cnpj', 'CNPJ da empresa'),
            ('enderecos', 'cep', 'CEP'),
            ('vehicles', 'chassi', 'Chassi'),
            ('vehicles', 'placa', 'Placa'),
            ('vehicles', 'cnae', 'CNAE')
        ]
        
        for table, column, description in critical_columns:
            query = f"""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = '{table}' AND column_name = '{column}'
            """
            
            result = await conn.fetchrow(query)
            
            if result:
                print(f"\n   [INFO] Tabela: {table}, Coluna: {column} ({description})")
                print(f"        Tipo: {result['data_type']}")
                if result['character_maximum_length']:
                    print(f"        Tamanho máximo: {result['character_maximum_length']}")
            else:
                print(f"\n   [ERRO] Coluna '{column}' não encontrada na tabela '{table}'!")
        
        # Verificar alguns valores de exemplo
        print("\n[INFO] Verificando valores de exemplo...")
        
        # CNPJ
        query = "SELECT cnpj FROM empresas LIMIT 3"
        rows = await conn.fetch(query)
        print(f"\n   [INFO] Exemplos de CNPJ:")
        for i, row in enumerate(rows):
            cnpj = row['cnpj']
            print(f"        [{i}] {cnpj} (tipo: {type(cnpj).__name__}, len: {len(str(cnpj))})")
        
        # CEP
        query = "SELECT cep FROM enderecos LIMIT 3"
        rows = await conn.fetch(query)
        print(f"\n   [INFO] Exemplos de CEP:")
        for i, row in enumerate(rows):
            cep = row['cep']
            print(f"        [{i}] {cep} (tipo: {type(cep).__name__}, len: {len(str(cep))})")
        
        # CNAE
        query = "SELECT cnae FROM vehicles LIMIT 3"
        rows = await conn.fetch(query)
        print(f"\n   [INFO] Exemplos de CNAE:")
        for i, row in enumerate(rows):
            cnae = row['cnae']
            print(f"        [{i}] {cnae} (tipo: {type(cnae).__name__}, len: {len(str(cnae))})")
        
        # Verificar contagem de registros
        print("\n[INFO] Contagem de registros...")
        
        tables = ['empresas', 'enderecos', 'contatos', 'marcas', 'modelos', 'vehicles', 'registrations']
        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table}"
            result = await conn.fetchrow(query)
            print(f"   {table}: {result['count']:,} registros")
        
    finally:
        await conn.close()
    
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO CONCLUÍDA")
    print("=" * 80)

if __name__ == '__main__':
    asyncio.run(check_data_types())
