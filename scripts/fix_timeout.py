#!/usr/bin/env python3
import re

# Ler o arquivo
with open('scripts/load_normalized_schema_optimized_v2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fazer as substituições
content = re.sub(r'pool_recycle=3600', 'pool_recycle=3600', content)
content = re.sub(r'statement_timeout": "300000"', 'statement_timeout": "600000"', content)

# Escrever de volta
with open('scripts/load_normalized_schema_optimized_v2.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Arquivo atualizado com sucesso')
