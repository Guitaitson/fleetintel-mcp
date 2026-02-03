#!/usr/bin/env python3
# Script para corrigir o timeout no load_normalized_schema_optimized_v2.py

file_path = 'scripts/load_normalized_schema_optimized_v2.py'

# Ler o arquivo
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fazer as substituições
content = content.replace('pool_recycle=3600', 'pool_recycle=3600')
content = content.replace('statement_timeout": "600000"', 'statement_timeout": "1800000"')  # 30 minutos

# Escrever de volta
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Arquivo atualizado com sucesso!')
print('Timeout aumentado para 30 minutos (1800000ms)')
