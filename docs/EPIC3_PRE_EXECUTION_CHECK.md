# 🔍 EPIC 3 - CHECKLIST PRÉ-EXECUÇÃO

**Data:** 2026-01-04 16:44  
**Arquivo:** Emplacamentos teste.xlsx (~283 MB)

---

## ⚠️ ALERTA CRÍTICO: EPIC 2 INCOMPLETO

**Status EPIC 2:** 83% (5 migrações pendentes)

### ❌ Migrações que PRECISAM ser aplicadas ANTES:

1. **Migração 02:** Deduplicação
   - Arquivo: `supabase/migrations/20260103000002_deduplicate_registrations.sql`
   
2. **Migração 03:** Índices adicionais
   - Arquivo: `supabase/migrations/20260103000003_add_indexes.sql`
   
3. **Migração 04:** Tabelas auxiliares
   - Arquivo: `supabase/migrations/20260103000004_auxiliary_tables.sql`
   
4. **Migração 05:** Views materializadas ⭐ CRÍTICO
   - Arquivo: `supabase/migrations/20260103000005_materialized_views.sql`
   - **Sem isso:** GT-29 (validação) vai FALHAR
   
5. **Migração 09:** Funções UPSERT ⭐ CRÍTICO
   - Arquivo: `supabase/migrations/20260103000009_upsert_functions.sql`
   - **Sem isso:** GT-28 (import) pode FALHAR

---

## ✅ CHECKLIST PRÉ-EXECUÇÃO

### Infraestrutura
- [x] Banco de dados Supabase conectado
- [ ] **EPIC 2 completo (11/11 migrações aplicadas)**
- [x] Scripts GT-26 a GT-30 criados
- [x] Dependências instaladas (pandas, openpyxl, tqdm)
- [x] Estrutura de diretórios criada

### Arquivo de Entrada
- [x] Arquivo existe: `data/raw/Emplacamentos teste.xlsx`
- [x] Tamanho: 283 MB
- [ ] Validação de estrutura (56 colunas)
- [ ] Total de linhas < 1.000.000
- [ ] Amostra de dados OK

### Configuração
- [x] `.env` configurado
- [x] DATABASE_URL presente
- [x] Espaço em disco suficiente

---

## 🎯 ORDEM DE EXECUÇÃO

### FASE 1: Completar EPIC 2 (MANUAL - 30 min)
**Ação:** Aplicar 5 migrações no Supabase SQL Editor

### FASE 2: Validar arquivo (automático - 5 min)
```bash
uv run python scripts/load_excel_to_csv.py
```

### FASE 3: Pipeline ETL (automático - variável)
```bash
# GT-26: Excel → CSV
uv run python scripts/load_excel_to_csv.py

# GT-27: Normalização
uv run python scripts/normalize_data.py

# GT-28: Import Supabase
uv run python scripts/load_to_supabase.py

# GT-29: Validação
uv run python scripts/validate_and_refresh.py

# GT-30: Quality Report
uv run python scripts/generate_quality_report.py
```

---

## 📊 TEMPO ESTIMADO

| Fase | Tempo |
|------|-------|
| EPIC 2 (manual) | 30 min |
| GT-26 (Excel→CSV) | 10-20 min |
| GT-27 (Normalização) | 15-30 min |
| GT-28 (Import) | 1-3 horas |
| GT-29 (Validação) | 5-10 min |
| GT-30 (Report) | 5 min |
| **TOTAL** | **~2-4 horas** |

---

## ⚠️ RECOMENDAÇÃO

**NÃO execute o pipeline antes de completar EPIC 2!**

Caso contrário:
- GT-28 pode falhar (sem UPSERT)
- GT-29 VAI falhar (sem views)
- Dados podem ficar inconsistentes
- Retrabalho necessário

**Próximo passo:** Aplicar migrações 02, 03, 04, 05, 09 no Supabase.
