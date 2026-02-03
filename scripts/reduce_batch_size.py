#!/usr/bin/env python3
# Script para reduzir o tamanho do batch de 1000 para 500

file_path = 'scripts/load_normalized_schema_optimized_v2.py'

# Ler o arquivo
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fazer as substituições
content = content.replace('batch_size = 1000', 'batch_size = 500')

# Escrever de volta
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Arquivo atualizado com sucesso!')
print('Batch size reduzido de 1000 para 500')
