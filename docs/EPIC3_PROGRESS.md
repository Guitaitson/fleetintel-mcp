# 📊 EPIC 3 - CARGA INICIAL - PROGRESSO

**Data:** 2026-01-04  
**Status:** 🔄 **EM ANDAMENTO (Fase 0 concluída)**

---

## ✅ FASE 0: PRÉ-REQUISITOS - COMPLETA

### Arquivos Validados
- ✅ **Excel:** `Sample-Emplacamentos.xlsx` - 3 registros, 56 colunas
- ✅ **CNAE:** `CNAE_TRAT.csv` - 1.343 registros, 16 colunas

### Infraestrutura Criada
- ✅ Estrutura de diretórios: `data/raw`, `data/processed`, `data/errors`, `reports`, `logs`
- ✅ Arquivos fonte movidos para `data/raw/`
- ✅ Dependências instaladas: `pandas`, `openpyxl`, `tqdm`, `sqlalchemy`

### Migrações Aplicadas
- ✅ **Migração 10:** `20260104000010_add_excel_fields.sql`
  - 37 novos campos adicionados à tabela `registrations`
  - 15 novos índices criados
  - Índice único composto: `(chassi, data_emplacamento)`
  
- ✅ **Migração 11:** `20260104000011_create_cnae_lookup.sql`
  - Tabela `cnae_lookup` criada
  - 7 índices criados
  - Função `get_cnae_info()` disponível

### Dados Carregados
- ✅ **CNAE:** 1.343 registros carregados na tabela `cnae_lookup`

---

## 📋 SCHEMA ATUAL DO BANCO

### Tabela `registrations`
**Total de campos:** ~60 campos (21 originais + 37 novos)

**Campos adicionados (Fase 0):**

**Veículo (6 campos):**
- cod_modelo, tracao, cilindrada, grupo_modelo, segmento, subsegmento

**Concessionária (4 campos):**
- cnpj_concessionario, concessionario, area_operacional, regiao_emplacamento

**Preço (2 campos):**
- preco, preco_validado

**Proprietário (8 campos):**
- tipo_proprietario, cpf_cnpj_proprietario, nome_proprietario
- data_abertura, idade_empresa, faixa_idade_empresa, segmento_cliente, porte

**Atividade Econômica (6 campos):**
- cod_atividade_economica, atividade_economica, cnae_agrupado
- codigo_natureza_juridica, natureza_juridica, grupo_locadora

**Endereço (7 campos):**
- logradouro, numero, complemento, bairro, cep, cidade_proprietario, uf_proprietario

**Contatos (1 campo JSONB):**
- contatos (telefones e celulares)

**API Real (6 campos):**
- cod_municipio, combustivel, potencia, data_emplacamento, data_atualizacao, email

### Tabela `cnae_lookup`
**Total de campos:** 19 campos
**Registros:** 1.343 CNAEs carregados

---

## 🎯 PRÓXIMAS FASES

### FASE 1: GT-26 - Pipeline Excel → CSV (PENDENTE)

**Script:** `scripts/load_excel_to_csv.py`

**Objetivo:** Converter Excel histórico (~600k no arquivo real) para CSV padronizado

**Funcionalidades necessárias:**
- Ler Excel em chunks de 50k linhas
- Validar 56 colunas esperadas
- Converter para CSV (UTF-8, delimiter `;`)
- Progress bar com tqdm
- Logging detalhado

**Saída:** `data/processed/emplacamentos_raw.csv`

**Tempo estimado:** 2-3 horas

---

### FASE 2: GT-27 - Normalização de Dados (PENDENTE)

**Script:** `scripts/normalize_data.py`

**Objetivo:** Limpar e normalizar dados para inserção no banco

**Transformações necessárias:**

1. **Datas:** Converter para ISO 8601 (YYYY-MM-DD)
2. **Documentos:** Remover formatação (apenas dígitos)
3. **Strings vazias:** Converter para NULL
4. **Preço:** Converter para DECIMAL
5. **Contatos:** Agrupar 14 campos em JSONB
6. **Campos calculados:**
   - `idade_empresa` (em dias)
   - `faixa_idade_empresa` (0-2, 2-5, 5-20, 20+ anos)

**Saída:** `data/processed/emplacamentos_normalized.csv`

**Tempo estimado:** 3-4 horas

---

### FASE 3: GT-28 - Importação Supabase (PENDENTE)

**Script:** `scripts/load_to_supabase.py`

**Objetivo:** Carregar dados normalizados no Supabase

**Funcionalidades necessárias:**
- UPSERT em batches de 1.000
- Retry automático (3x with exponential backoff)
- Progress tracking detalhado
- Logging por batch
- Salvar erros em `data/errors/failed_records.csv`

**Chave UPSERT:** `(chassi, data_emplacamento)` com fallback para `external_id`

**Tempo estimado:** 4-6 horas (execução)

---

### FASE 4: GT-29 - Validação e Refresh (PENDENTE)

**Script:** `scripts/validate_and_refresh.py`

**Validações:**
- Contagem total (~600k esperado)
- Zero duplicatas
- Distribuição temporal coerente
- Integridade referencial
- Performance de queries (< 100ms médio)
- Refresh de views materializadas

**Tempo estimado:** 1-2 horas

---

### FASE 5: GT-30 - Quality Report (PENDENTE)

**Script:** `scripts/generate_quality_report.py`

**Métricas:**
- % NULL por coluna
- Datas/documentos inválidos
- Consistência de dados
- Distribuições (marca, UF, ano)
- Quality Score (0-100)

**Saídas:**
- `reports/quality_report_600k.json`
- `reports/quality_report_600k.md`

**Tempo estimado:** 2-3 horas

---

## 📝 SCRIPTS CRIADOS

### Infraestrutura
1. ✅ `scripts/validate_source_files.py` - Validação de arquivos fonte
2. ✅ `scripts/apply_migrations.py` - Aplicar migrações
3. ✅ `scripts/load_cnae_data.py` - Carregar dados CNAE

### ETL Pipeline (Pendentes)
4. ⏳ `scripts/load_excel_to_csv.py` - GT-26
5. ⏳ `scripts/normalize_data.py` - GT-27
6. ⏳ `scripts/load_to_supabase.py` - GT-28
7. ⏳ `scripts/validate_and_refresh.py` - GT-29
8. ⏳ `scripts/generate_quality_report.py` - GT-30

---

## 🚧 OBSERVAÇÕES IMPORTANTES

### 1. Arquivo Excel Sample
O arquivo atual (`Sample-Emplacamentos.xlsx`) tem apenas **3 registros** para teste. 
- Este é um arquivo de amostra para validar a estrutura
- O arquivo completo terá ~600k registros

### 2. Colunas Extras no Excel
O Excel tem **56 colunas** (não 54 como planejado):
- Colunas extras identificadas: "Subclasse Tratado" e "SalesForce"
- Já mapeadas no schema do banco

### 3. Chave UPSERT
Implementada com índice único composto:
- `(chassi, data_emplacamento)` - preferencial
- `external_id` - fallback para casos sem chassi/data

### 4. Performance
Com os índices criados, esperamos:
- Busca por placa: < 50ms
- Busca por CNPJ: < 100ms
- Agregação por marca: < 500ms

---

## ⏱️ TEMPO ESTIMADO RESTANTE

| Fase | Estimativa |
|------|------------|
| GT-26 (Excel → CSV) | 2-3h |
| GT-27 (Normalização) | 3-4h |
| GT-28 (Import) | 4-6h |
| GT-29 (Validação) | 1-2h |
| GT-30 (Quality Report) | 2-3h |
| **TOTAL** | **12-18 horas** |

---

## 🎯 PRÓXIMO PASSO RECOMENDADO

**Criar script GT-26** (`load_excel_to_csv.py`) para iniciar o pipeline ETL.

Este script será o primeiro passo do pipeline de dados e permitirá validar a estrutura completa do Excel antes de prosseguir com a normalização e carga.

---

**Atualizado em:** 2026-01-04 15:42:00
