# 📊 STATUS DO REDESIGN - Database V2

**Data:** 2026-01-04 18:40  
**Status:** Migration 12 preparada (timeout ao aplicar via script)

---

## ✅ O QUE FOI FEITO

### 1. **Análise Completa dos Problemas**
- ✅ Schema monolítico (60+ campos em 1 tabela)
- ✅ Tipos errados (CNPJ perde zeros: `02916265009116` → `2916265009116`)
- ✅ Sem relacionamentos (CNAE_LOOKUP sem FK)
- ✅ Falta integração BrasilAPI
- ✅ Performance ruim (150s/batch = 40h para 974k)

### 2. **Nova Arquitetura Projetada**
- ✅ Schema normalizado 3NF em `docs/DATABASE_REDESIGN_V2.md`
- ✅ 7 tabelas principais:
  - `marcas` (domínio)
  - `modelos` (domínio)
  - `vehicles` (veículos)
  - `empresas` (CNPJ + BrasilAPI)
  - `enderecos` (CEP + geolocalização)
  - `contatos` (telefones/emails)
  - `registrations` (núcleo)

### 3. **Migration 12 Criada**
- ✅ Arquivo: `supabase/migrations/20260104000012_reset_normalized_schema.sql`
- ✅ DROP completo do schema antigo
- ✅ CREATE novo schema normalizado
- ✅ Função `fix_documento()` para corrigir CNPJ/CEP
- ✅ Índices otimizados
- ✅ FKs e relacionamentos corretos
- ⚠️  **NÃO APLICADA** (timeout via script)

---

## ⚠️ PROBLEMA ATUAL

**Timeout ao aplicar Migration 12:**
```
asyncpg.exceptions.QueryCanceledError: 
canceling statement due to statement timeout
```

**Causa:** Migration muito grande (DROP + CREATE de 8 tabelas + índices) em uma transação.

---

## 🔧 PRÓXIMOS PASSOS (MANUAL)

### **Opção A: Aplicar via Supabase Dashboard** (Recomendado)

1. Acessar **Supabase Dashboard** → SQL Editor
2. Copiar conteúdo de `supabase/migrations/20260104000012_reset_normalized_schema.sql`
3. Colar e **executar manualmente**
4. Verificar se 8 tabelas foram criadas:
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   ORDER BY table_name;
   ```

### **Opção B: Dividir Migration em Partes**

Criar múltiplas migrations menores:
- `12a_drop_old_schema.sql` (só DROPs)
- `12b_create_functions.sql` (funções)
- `12c_create_domain_tables.sql` (marcas, modelos)
- `12d_create_main_tables.sql` (vehicles, empresas, etc)
- `12e_create_indexes.sql` (índices)

### **Opção C: Usar Supabase CLI**

```bash
supabase db reset --linked
supabase db push
```

---

## 📋 APÓS APLICAR MIGRATION 12

### 1. **Verificar Schema**
```sql
-- Verificar tabelas
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name = t.table_name) as num_columns
FROM information_schema.tables t
WHERE table_schema = 'public'
ORDER BY table_name;

-- Verificar FKs
SELECT 
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

### 2. **Criar Script ETL**

Próximo arquivo a criar: `scripts/load_normalized_schema.py`

**Fluxo:**
1. Ler CSV normalizado
2. Extrair e inserir marcas únicas
3. Extrair e inserir modelos únicos
4. Inserir vehicles (com FKs para marcas/modelos)
5. Inserir empresas (com CNPJ corrigido via `fix_documento`)
6. Inserir endereços
7. Inserir contatos
8. Inserir registrations (com FKs)

**Target:** <1 hora para 974k registros

### 3. **Implementar Enriquecimento BrasilAPI**

Criar jobs assíncronos:
- `jobs/enrich_cnpj.py` (CNPJ → BrasilAPI)
- `jobs/enrich_cep.py` (CEP → BrasilAPI + geolocalização)

---

## 📊 ARQUIVOS CRIADOS

```
docs/
  ├─ DATABASE_REDESIGN_V2.md           ← Design completo
  └─ REDESIGN_STATUS.md                ← Este arquivo

supabase/migrations/
  └─ 20260104000012_reset_normalized_schema.sql   ← Migration (não aplicada)
```

---

## 🎯 DECISÃO NECESSÁRIA

**Qual caminho seguir para aplicar a Migration 12?**

- [ ] **Opção A:** Aplicar manualmente via Supabase Dashboard
- [ ] **Opção B:** Dividir em migrations menores
- [ ] **Opção C:** Usar Supabase CLI

**Após aplicar, podemos:**
1. Criar script ETL otimizado
2. Testar com 10k registros
3. Executar carga completa 974k
4. Ativar enriquecimento BrasilAPI

---

## 💡 NOTAS IMPORTANTES

1. **Dados atuais serão perdidos** (apenas ~100 registros com problemas)
2. **CNPJ será corrigido** (14 dígitos com zeros à esquerda)
3. **Performance esperada:** 270+ reg/s (vs 6 reg/s atual)
4. **Integridade garantida** por FKs
5. **Pronto para escalar** para milhões de registros

---

**Aguardando decisão sobre como aplicar Migration 12...**
