# Plano de Reorganização do Projeto

**Data:** 2026-02-04
**Status:** DIAGNÓSTICO CONCLUÍDO

---

## Diagnóstico: Estado Atual

### Problemas Identificados

#### 1. Scripts Duplicados (15+ arquivos)

| Categoria | Arquivos Duplicados | Versão Ativa |
|-----------|---------------------|--------------|
| Carga Normalizada | `load_normalized_schema*.py` (7 arquivos) | `v7.py` |
| Carga Supabase | `load_to_supabase*.py` (4 arquivos) | `FINAL.py` |
| Normalização | `normalize_data*.py` (2 arquivos) | `optimized.py` |
| Excel → CSV | `load_excel_to_csv*.py` (2 arquivos) | `optimized.py` |
| Análise RAW | `analyze_raw_data*.py` (3 arquivos) | `v3.py` |
| DB Counts | `check_db_counts*.py` (3 arquivos) | `v2.py` |
| Testes ETL | `test_etl*.py` (múltiplos) | - |

**TOTAL:** ~25+ scripts duplicados/obsoletos

#### 2. Documentação Fragmentada (20+ arquivos)

| Categoria | Arquivos | Status |
|-----------|----------|--------|
| Status/Checkpoint | `STATUS_*.md`, `CHECKPOINT_*.md`, `FINAL_*.md` | 10+ arquivos temporários |
| ETL Reports | `ETL_*.md`, `VALIDATION_*.md` | 8+ arquivos temporários |
| Root Cause | `ROOT_CAUSE_*.md` | 2+ arquivos temporários |
| Documentação Válida | `README.md`, `PROJECT_STATUS.md`, `ROADMAP.md` | 5 arquivos |

**TOTAL:** ~30+ documentos temporários/obsoletos

#### 3. Estrutura de Pastas Inconsistente

```
scripts/          # Mistura de scripts de produção + debug + investigação
  ├── *.py (90+ arquivos)
  ├── *.sh
  └── *.sql
docs/             # Mistura de docs importantes + temporários
  ├── *.md (40+ arquivos)
  └── api/ architecture/ git/ policies/ setup/
```

---

## Estrutura Proposta

### Scripts (scripts/)

```
scripts/
├── etl/                          # Scripts de produção (ETL)
│   ├── load_excel_to_csv.py      # Excel → CSV Raw
│   ├── normalize_data.py          # CSV Raw → CSV Normalized
│   ├── load_normalized.py        # CSV Normalized → PostgreSQL
│   └── clean_database.py          # Limpar banco
├── db/                           # Scripts de banco
│   ├── apply_migrations.py        # Aplicar migrations
│   ├── validate_schema.py         # Validar schema
│   └── db_health.py               # Saúde do banco
├── api/                          # Scripts de API
│   ├── test_connection.py        # Testar conexão
│   └── test_api.py               # Testar API
└── utils/                        # Utilitários
    ├── validate_env.py            # Validar variáveis de ambiente
    └── README.md                  # Documentação
```

### Documentação (docs/)

```
docs/
├── README.md                      # Visão geral do projeto
├── PROJECT_STATUS.md              # Estado atual do projeto
├── ROADMAP.md                    # Roadmap de desenvolvimento
├── ARCHITECTURE.md               # Arquitetura técnica
├── SETUP.md                      # Guia de configuração
├── development.md                # Guia de desenvolvimento
├── api/                          # Documentação da API
│   └── *.md
├── git/                          # Politicas Git
│   └── *.md
└── policies/                     # Políticas do projeto
    └── *.md
```

### Arquivos Temporários/Arquivo Morto

Mover para `.archive/`:
- `scripts/load_normalized_schema_v1-v6.py`
- `scripts/load_to_supabase_v1-v3.py`
- `scripts/analyze_raw_data*.py`
- `scripts/check_db_counts*.py`
- `scripts/test_etl*.py` (exceto principais)
- `docs/CHECKPOINT_*.md`
- `docs/STATUS_REPORT_*.md`
- `docs/ETL_*.md`
- `docs/VALIDATION_*.md`
- `docs/ROOT_CAUSE_*.md`
- `docs/*_FINAL_STATUS.md`

---

## Plano de Execução

### Fase 1: Arquivar Arquivos Obsoletos
1. Criar pasta `.archive/`
2. Mover scripts duplicados/obsoletos
3. Mover documentos temporários
4. Criar índice do arquivo morto

### Fase 2: Limpar Scripts
1. Manter apenas versões ativas
2. Remover versões antigas
3. Consolidar scripts similares

### Fase 3: Reorganizar Docs
1. Manter apenas documentação essencial
2. Consolidar informações duplicadas
3. Criar estrutura de pastas lógica

### Fase 4: Atualizar README
1. Criar índice de scripts
2. Criar índice de documentação
3. Adicionar links para documentação

---

## Scripts a Manter (Ativos)

### ETL (Produção)
- [x] `scripts/load_excel_to_csv_optimized.py`
- [x] `scripts/normalize_data_optimized.py`
- [x] `scripts/load_normalized_schema_optimized_v7.py`
- [x] `scripts/clean_database.py`

### Database
- [x] `scripts/apply_migrations.py`
- [x] `scripts/validate_migrations.py`
- [x] `scripts/db_health.py`

### Utilitários
- [x] `scripts/validate_env.py`
- [x] `scripts/test_connection.py`

---

## Scripts a Arquivar (Obsoletos)

### ETL (7+ arquivos)
- `load_normalized_schema.py` (original)
- `load_normalized_schema_optimized.py` (v1)
- `load_normalized_schema_optimized_v2.py` - v6
- `load_to_supabase*.py` (4 versões)
- `load_excel_to_csv.py` (original)

### Análise/Debug (15+ arquivos)
- `analyze_raw_data*.py` (3 versões)
- `check_db_counts*.py` (3 versões)
- `test_etl*.py` (múltiplos)
- `investigate_root_cause.py`
- `debug_etl.py`
- `diagnose_*.py`
- `fix_*.py` (múltiplos)

---

## Documentação a Arquivar (20+ arquivos)

### Status/Checkpoint
- `CHECKPOINT_2026-02-04.md`
- `STATUS_REPORT_*.md` (5+ arquivos)
- `FINAL_STATUS_*.md` (2+ arquivos)
- `EPIC*_STATUS.md` (5+ arquivos)

### ETL/Validation
- `ETL_LOAD_STATUS_*.md`
- `ETL_CORRECTION_PLAN_*.md`
- `ETL_OPTIMIZATION_*.md`
- `VALIDATION_REPORT_*.md`
- `ROOT_CAUSE_*.md`
- `DATA_TYPE_*.md`

---

## Ações Imediatas

1. Criar arquivo `.archive/README.md` com índice
2. Mover arquivos obsoletos para `.archive/`
3. Atualizar `.gitignore` para ignorar `.archive/`
4. Atualizar `scripts/README.md`
5. Criar `docs/README.md` com índice

---

## Conclusão

O projeto tem ~50+ arquivos duplicados/obsoletos que devem ser arquivados para melhorar a organização e clareza.
