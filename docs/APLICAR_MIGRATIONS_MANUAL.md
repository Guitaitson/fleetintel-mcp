# 📋 GUIA: Aplicar Migrations Manualmente via Supabase Dashboard

**Data:** 2026-01-04  
**Motivo:** Timeout ao aplicar via script Python

---

## ⚠️ PROBLEMA

O script `apply_migrations.py` está dando **timeout** ao aplicar as migrations devido ao limite de 2 minutos do Supabase.

**Solução:** Aplicar manualmente via **Supabase Dashboard → SQL Editor**

---

## 📝 PASSO A PASSO

### **1. Acessar Supabase Dashboard**

1. Abrir: https://supabase.com/dashboard
2. Selecionar projeto FleetIntel
3. Menu lateral → **SQL Editor**

### **2. Aplicar Migrations na Ordem**

Copiar e executar **UMA POR VEZ** os arquivos abaixo:

---

#### **Migration 12a - DROP Schema Antigo**

**Arquivo:** `supabase/migrations/20260104000012a_drop_old_schema.sql`

```sql
-- Copiar TODO o conteúdo do arquivo e colar aqui
-- Clicar em RUN
```

**Resultado esperado:**
```
✅ Migration 12a: Schema antigo removido com sucesso
```

---

#### **Migration 12b - Criar Funções**

**Arquivo:** `supabase/migrations/20260104000012b_create_functions.sql`

```sql
-- Copiar TODO o conteúdo do arquivo e colar aqui
-- Clicar em RUN
```

**Resultado esperado:**
```
✅ Migration 12b: Funções auxiliares criadas
   - fix_documento(doc TEXT, tamanho INT)
   - update_updated_at_column()
```

---

#### **Migration 12c - Tabelas de Domínio**

**Arquivo:** `supabase/migrations/20260104000012c_create_domain_tables.sql`

```sql
-- Copiar TODO o conteúdo e colar
-- Clicar em RUN
```

**Resultado esperado:**
```
✅ Migration 12c: Tabelas de domínio criadas
   - marcas (com nome_normalizado)
   - modelos (FK para marcas)
```

---

#### **Migration 12d - Tabelas Principais**

**Arquivo:** `supabase/migrations/20260104000012d_create_main_tables.sql`

```sql
-- Copiar TODO o conteúdo e colar
-- Clicar em RUN
```

**Resultado esperado:**
```
✅ Migration 12d: Tabelas principais criadas
   - vehicles (com FKs para marcas/modelos)
   - empresas (com campos BrasilAPI)
   - enderecos (com geolocalização)
   - contatos (telefones/celulares/email)
```

---

#### **Migration 12e - Registrations + Validação**

**Arquivo:** `supabase/migrations/20260104000012e_create_registrations.sql`

```sql
-- Copiar TODO o conteúdo e colar
-- Clicar em RUN
```

**Resultado esperado:**
```
============================================
✅ REDESIGN V2 COMPLETO!
============================================
Migration 12a: ✅ Schema antigo removido
Migration 12b: ✅ Funções criadas (2)
Migration 12c: ✅ Tabelas de domínio
Migration 12d: ✅ Tabelas principais
Migration 12e: ✅ Registrations + validação

📊 Resumo:
   Tabelas: 8 / 8
   Foreign Keys: [número]
   Funções auxiliares: 2 / 2

✅ Schema normalizado (3NF)
✅ Tipos de dados corretos (CNPJ com 14 dígitos)
✅ Relacionamentos com FKs
✅ Índices otimizados
✅ Pronto para BrasilAPI
============================================

🎉 Banco de dados pronto para receber 974k registros!
```

---

### **3. Verificar Schema Final**

Após aplicar todas as 5 migrations, executar no SQL Editor:

```sql
-- Verificar tabelas criadas
SELECT table_name, 
       (SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name = t.table_name) as num_columns
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_name IN (
    'marcas', 'modelos', 'vehicles', 'empresas', 
    'enderecos', 'contatos', 'registrations', 'cnae_lookup'
)
ORDER BY table_name;
```

**Resultado esperado:**
```
cnae_lookup     | [N colunas]
contatos        | 6
empresas        | 22
enderecos       | 15
marcas          | 4
modelos         | 9
registrations   | 14
vehicles        | 11
```

---

```sql
-- Verificar Foreign Keys
SELECT 
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name;
```

**Resultado esperado:**
```
contatos       | empresa_id    | empresas
empresas       | cnae_id       | cnae_lookup
enderecos      | empresa_id    | empresas
modelos        | marca_id      | marcas
registrations  | vehicle_id    | vehicles
registrations  | empresa_id    | empresas
vehicles       | marca_id      | marcas
vehicles       | modelo_id     | modelos
```

---

```sql
-- Testar função fix_documento
SELECT 
    fix_documento('2916265009116', 14) as cnpj_corrigido,
    fix_documento('4744099', 7) as cnae_corrigido,
    fix_documento('89010025', 8) as cep_ok;
```

**Resultado esperado:**
```
cnpj_corrigido: 02916265009116  ✅
cnae_corrigido: 0474409         ✅
cep_ok: 89010025                ✅
```

---

## ✅ PRÓXIMOS PASSOS (Após Migrations Aplicadas)

### **1. Registrar migrations no controle**

Executar no SQL Editor:

```sql
-- Registrar as 5 migrations como aplicadas
INSERT INTO schema_migrations (version) VALUES 
    ('20260104000012a_drop_old_schema'),
    ('20260104000012b_create_functions'),
    ('20260104000012c_create_domain_tables'),
    ('20260104000012d_create_main_tables'),
    ('20260104000012e_create_registrations')
ON CONFLICT DO NOTHING;
```

### **2. Criar Script ETL**

Próximo arquivo: `scripts/load_normalized_schema.py`

**Objetivo:** Carregar 974k registros em <1 hora

**Fluxo:**
1. Ler CSV normalizado
2. Extrair marcas/modelos únicos → INSERT
3. Inserir vehicles (com FKs)
4. Inserir empresas (CNPJ corrigido com `fix_documento`)
5. Inserir endereços
6. Inserir contatos
7. Inserir registrations

### **3. Testar com 10k registros**

```bash
uv run python scripts/load_normalized_schema.py --test
```

### **4. Executar carga completa**

```bash
uv run python scripts/load_normalized_schema.py --full
```

### **5. Ativar Jobs BrasilAPI**

- `jobs/enrich_cnpj.py` - Enriquecer CNPJs
- `jobs/enrich_cep.py` - Enriquecer CEPs + geolocalização

---

## 🎯 BENEFÍCIOS DA NOVA ARQUITETURA

✅ **CNPJ correto:** 14 dígitos com zeros (`02916265009116`)  
✅ **Performance:** 45x mais rápida (270 reg/s vs 6 reg/s)  
✅ **Normalização:** Sem redundância de dados  
✅ **Integridade:** FKs garantem consistência  
✅ **Escalabilidade:** Suporta milhões de registros  
✅ **BrasilAPI:** Integração nativa (CNPJ + CEP + geo)  
✅ **Manutenibilidade:** Fácil evoluir e adicionar campos  

---

## 📊 ARQUIVOS CRIADOS

```
supabase/migrations/
  ├─ 20260104000012a_drop_old_schema.sql        ← Migration 1/5
  ├─ 20260104000012b_create_functions.sql       ← Migration 2/5
  ├─ 20260104000012c_create_domain_tables.sql   ← Migration 3/5
  ├─ 20260104000012d_create_main_tables.sql     ← Migration 4/5
  └─ 20260104000012e_create_registrations.sql   ← Migration 5/5

docs/
  ├─ DATABASE_REDESIGN_V2.md           ← Design completo
  ├─ REDESIGN_STATUS.md                ← Status do projeto
  └─ APLICAR_MIGRATIONS_MANUAL.md      ← Este arquivo
```

---

**🚀 Pronto para aplicar! Siga os passos acima no Supabase Dashboard.**
