# Resumo das Estratégias de Otimização ETL

**Data**: 2026-02-02 16:23 BRT  
**Objetivo**: Reduzir tempo de carga de 40+ dias para < 1 hora

---

## 📊 Diagnóstico do Problema

### Gargalos Identificados

| # | Gargalo | Localização | Impacto |
|---|----------|-------------|----------|
| 1 | **Inserções row-by-row** | `load_normalized_schema.py` | 1.1M queries = 15.3h+ |
| 2 | **Pool size pequeno** | `load_normalized_schema.py:23` | Apenas 15 conexões |
| 3 | **Processamento lento Pandas** | `normalize_data.py` | 3-4h de `apply()` |
| 4 | **Leitura Excel sem chunking** | `load_excel_to_csv.py:124` | 1GB+ na memória |
| 5 | **Falta de índices temporários** | Todas tabelas | Lookups O(n) |

### Cálculo do Tempo Atual

```
Vehicles:    10k registros × 1 query/veh  = 10k queries  × 50ms = 8.3 min
Empresas:    50k registros × 3 queries/emp = 150k queries × 50ms = 2.1 h
Registrations: 974k registros × 1 query/reg = 974k queries × 50ms = 13.5 h
Normalização: 974k registros × apply() lento = 3-4 h
─────────────────────────────────────────────────────────────────────────────
TOTAL: ~19 horas (teórico) → 40+ dias (prático com overhead)
```

---

## 🚀 Estratégias de Otimização

### Estratégia #1: Batch Inserts (MELHORIA 50x) ⭐ CRÍTICO

**O que é**: Agrupar múltiplos inserts em uma única query

**Antes**:
```python
for _, row in df.iterrows():
    await conn.execute(stmt, {"chassi": row['chassi'], ...})
# 974k queries individuais
```

**Depois**:
```python
batch_size = 1000
params = [{"chassi": row['chassi'], ...} for _, row in df.iterrows()]
for i in range(0, len(params), batch_size):
    await conn.execute(stmt, params[i:i+batch_size])
# 974 queries (1000x menos!)
```

**Impacto**: 15.3h → 18 minutos

---

### Estratégia #2: COPY Command (MELHORIA 100x) ⭐ CRÍTICO

**O que é**: Usar comando nativo `COPY` do PostgreSQL

**Implementação**:
```python
from io import StringIO

def copy_from_csv(conn, table_name, csv_path):
    with conn.cursor() as cur:
        with open(csv_path, 'r') as f:
            cur.copy_expert(
                f"COPY {table_name} FROM STDIN WITH CSV HEADER DELIMITER ';'",
                f
            )
```

**Impacto**: 15.3h → 9 minutos

---

### Estratégia #3: Aumentar Pool Size (MELHORIA 3x)

**O que é**: Aumentar número de conexões simultâneas

**Antes**:
```python
pool_size=5, max_overflow=10  # Total: 15 conexões
```

**Depois**:
```python
pool_size=20, max_overflow=30  # Total: 50 conexões
```

**Impacto**: 18 min → 6 minutos

---

### Estratégia #4: Vectorização Pandas (MELHORIA 20x)

**O que é**: Substituir `apply()` por operações vetorizadas

**Antes**:
```python
df['contatos'] = df.progress_apply(create_contacts_json, axis=1)
# Processa 974k linhas sequencialmente em Python
```

**Depois**:
```python
# Operações vetorizadas em C
df['cpf_cnpj_proprietario'] = (
    df['DOCUMENTO']
    .astype(str)
    .str.extract(r'(\d+)')[0]
    .str.zfill(14)
)
```

**Impacto**: 3-4h → 9-12 minutos

---

### Estratégia #5: Índices Temporários (MELHORIA 10x)

**O que é**: Criar índices antes da carga para acelerar lookups

**Implementação**:
```python
# Antes da carga
await conn.execute(text("CREATE INDEX IF NOT EXISTS temp_vehicles_chassi ON vehicles(chassi)"))
await conn.execute(text("CREATE INDEX IF NOT EXISTS temp_empresas_cnpj ON empresas(cnpj)"))

# Fazer carga...

# Depois da carga (opcional)
await conn.execute(text("DROP INDEX IF EXISTS temp_vehicles_chassi"))
await conn.execute(text("DROP INDEX IF EXISTS temp_empresas_cnpj"))
```

**Impacto**: Lookups O(n) → O(log n)

---

## 📈 Projeção de Melhorias

### Cenário Atual (Baseline)
| Etapa | Registros | Queries | Tempo |
|--------|-----------|----------|--------|
| Vehicles | 10k | 10k | 8.3 min |
| Empresas | 50k | 150k | 2.1 h |
| Registrations | 974k | 974k | 13.5 h |
| Normalização | 974k | - | 3-4 h |
| **TOTAL** | **974k** | **1.1M** | **~19 h** |

### Cenário Otimizado (Fase 1: Batch Inserts)
| Etapa | Registros | Queries | Tempo | Melhoria |
|--------|-----------|----------|--------|----------|
| Vehicles | 10k | 10 | 10 seg | 50x |
| Empresas | 50k | 150 | 2 min | 63x |
| Registrations | 974k | 974 | 5 min | 162x |
| Normalização | 974k | - | 3-4 h | 1x |
| **TOTAL** | **974k** | **1.1k** | **~3.5 h** | **5.4x** |

### Cenário Otimizado (Todas Fases)
| Etapa | Registros | Queries | Tempo | Melhoria |
|--------|-----------|----------|--------|----------|
| Vehicles | 10k | 10 | 10 seg | 50x |
| Empresas | 50k | 150 | 2 min | 63x |
| Registrations | 974k | 974 | 5 min | 162x |
| Normalização | 974k | - | 10 min | 24x |
| **TOTAL** | **974k** | **1.1k** | **~17 min** | **67x** |

### Cenário com COPY Command
| Etapa | Registros | Tempo | Melhoria |
|--------|-----------|--------|----------|
| Vehicles | 10k | 5 seg | 100x |
| Empresas | 50k | 1 min | 126x |
| Registrations | 974k | 3 min | 270x |
| Normalização | 974k | 10 min | 24x |
| **TOTAL** | **974k** | **~14 min** | **82x** |

---

## 🎯 Plano de Implementação

### Fase 1: Batch Inserts (PRIORIDADE MÁXIMA)
**Tempo**: 2-3 horas  
**Impacto**: 19h → 3.5h (5.4x)

**Tarefas**:
1. ✅ Modificar `load_vehicles()` para batch inserts
2. ✅ Modificar `load_empresas_enderecos_contatos()` para batch inserts
3. ✅ Modificar `load_registrations()` para batch inserts
4. ✅ Aumentar pool size para 20+30
5. ✅ Adicionar índices temporários

**Arquivo**: `scripts/load_normalized_schema.py`

---

### Fase 2: Vectorização Pandas
**Tempo**: 1-2 horas  
**Impacto**: 3-4h → 10 min (24x)

**Tarefas**:
1. ✅ Vectorizar `create_contacts_json()`
2. ✅ Vectorizar normalizações (CNPJ, CEP, CNAE)
3. ✅ Remover `progress_apply()` lento

**Arquivo**: `scripts/normalize_data.py`

---

### Fase 3: COPY Command
**Tempo**: 2-3 horas  
**Impacto**: 3.5h → 14 min (15x adicional)

**Tarefas**:
1. ✅ Implementar `copy_from_csv()` para cada tabela
2. ✅ Criar CSVs temporários otimizados
3. ✅ Integrar com pipeline ETL

**Arquivo**: `scripts/load_with_copy.py` (novo)

---

### Fase 4: Testes e Validação
**Tempo**: 1-2 horas

**Tarefas**:
1. ✅ Criar script de benchmark
2. ✅ Testar com 100 registros
3. ✅ Testar com 10k registros
4. ✅ Validar integridade dos dados
5. ✅ Comparar tempos antes/depois

---

## ✅ Checklist de Validação

### Antes da Implementação
- [ ] Backup do banco de dados atual
- [ ] Documentar tempo atual de carga (baseline)
- [ ] Testar carga com 100 registros (sucesso esperado: 98%)

### Durante Implementação
- [ ] Fase 1: Batch implements
- [ ] Fase 2: Vectorização Pandas
- [ ] Fase 3: COPY command
- [ ] Fase 4: Testes

### Após Implementação
- [ ] Testar com 100 registros
- [ ] Testar com 10k registros
- [ ] Validar integridade dos dados
- [ ] Comparar tempos antes/depois
- [ ] Documentar resultados
- [ ] Atualizar `PROJECT_STATUS.md`

---

## 📊 Métricas de Sucesso

| Métrica | Antes | Meta (Fase 1) | Meta (Todas Fases) |
|----------|-------|----------------|-------------------|
| Tempo Total | 19h+ | < 4h | < 30 min |
| Throughput | 14 reg/s | > 70 reg/s | > 500 reg/s |
| Queries | 1.1M | < 10k | < 1k |
| RAM Peak | 1GB+ | < 500MB | < 200MB |
| Sucesso Carga | 98% | > 99% | > 99% |

---

## 🎓 Recursos Adicionais

### Bibliotecas Necessárias
```bash
# Para COPY command
uv pip install psycopg2-binary

# Para wrapper simplificado (opcional)
uv pip install pgcopy
```

### Comandos Úteis
```sql
-- Monitorar queries lentas
SELECT * FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;

-- Verificar tamanho de tabelas
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Verificar índices
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'registrations';
```

---

## 🚦 Conclusão

**Resumo**:
- **Problema**: 40+ dias para carregar 974k registros
- **Causa Raiz**: Inserções row-by-row (1.1M queries)
- **Solução**: Batch inserts + vectorização + COPY command
- **Resultado Esperado**: 19h → 14 min (**82x mais rápido**)

**Próximos Passos**:
1. Implementar Fase 1 (batch inserts) - **PRIORIDADE MÁXIMA**
2. Implementar Fase 2 (vectorização Pandas)
3. Implementar Fase 3 (COPY command)
4. Executar testes e validação

---

**Documento criado em**: 2026-02-02 16:23 BRT
