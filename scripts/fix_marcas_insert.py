#!/usr/bin/env python3
# Script para corrigir a inserção de marcas para evitar timeout

file_path = 'scripts/load_normalized_schema_optimized_v2.py'

# Ler o arquivo
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Substituir a inserção em lote de marcas por inserção individual
old_code = '''    # Inserir marcas em lote (batch insert)
    if len(marcas_unicas) > 0:
        # Usar sempre ON CONFLICT para evitar problemas de timeout
        stmt = text("""
            INSERT INTO marcas (nome)
            VALUES (:nome)
            ON CONFLICT (nome) DO NOTHING
        """)
        params = [{"nome": marca} for marca in marcas_unicas]
        await conn.execute(stmt, params)
        print("   Marcas inseridas em lote")'''

new_code = '''    # Inserir marcas individualmente para evitar timeout
    if len(marcas_unicas) > 0:
        stmt = text("""
            INSERT INTO marcas (nome)
            VALUES (:nome)
            ON CONFLICT (nome) DO NOTHING
        """)
        for marca in marcas_unicas:
            await conn.execute(stmt, {"nome": marca})
        print(f"   {len(marcas_unicas)} marcas inseridas individualmente")'''

content = content.replace(old_code, new_code)

# Escrever de volta
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Arquivo atualizado com sucesso!')
print('Inserção de marcas alterada de batch para individual')
