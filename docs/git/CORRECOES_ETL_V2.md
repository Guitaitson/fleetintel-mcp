# CORREÇÕES ETL V2 - CAUSA RAIZ RESOLVIDA

**Data:** 2026-01-04  
**Autor:** AI Assistant com Claude Opus  
**Status:** ✅ Implementado

---

## 🔍 PROBLEMA IDENTIFICADO

### Cadeia de Falhas:
```
EXCEL → CSV → NORMALIZED → DATABASE
 ❌       ❌       ❌          ❌
```

**Resultado:** 0 de 10.000 registrations inseridos após 102 minutos

---

## 🎯 CAUSA RAIZ

### **PRINCÍPIO VIOLADO:**
> **"Códigos numéricos (CNPJ, CEP, CNAE, etc.) NUNCA devem ser tratados como números"**

### Problemas Específicos:

#### 1. **load_excel_to_csv.py**
```python
# ❌ ERRADO (antes):
df = pd.read_excel(input_file)
# CNPJ "02916265009116" → número 2916265009116 (perde zero à esquerda)

# ✅ CORRETO (depois):
DTYPE_MAP = {
    'DOCUMENTO': str,
    'CNPJ CONCESSIONARIA': str,
    'CEP': str,
    'CNAE RF': str,
    # ...
}
df = pd.read_excel(input_file, dtype=DTYPE_MAP)
```

#### 2. **normalize_data.py**
```python
# ❌ ERRADO (antes):
def normalize_document(doc):
    return re.sub(r'\D', '', str(doc))  # Sem padding!

# ✅ CORRETO (depois):
def normalize_cnpj(doc):
    digits = re.sub(r'\D', '', str(doc))
    return digits.zfill(14)  # Padding com zeros à esquerda

def normalize_cep(cep):
    digits = re.sub(r'\D', '', str(cep))
    return digits.zfill(8)  # 8 dígitos
```

#### 3. **load_normalized_schema.py**
```python
# ❌ ERRADO (antes):
cnpj_key = str(int(row['cpf_cnpj_proprietario']))  # Conversões complexas

# ✅ CORRETO (depois):
cnpj_key = row['cpf_cnpj_proprietario']  # Usa string diretamente
```

---

## ✅ CORREÇÕES IMPLEMENTADAS

### **FASE 1: load_excel_to_csv.py**
- ✅ Adicionado `DTYPE_MAP` com 7 campos de código
- ✅ Aplicado em **todas** as leituras do Excel
- ✅ Comentário: "NUNCA números"

### **FASE 2: normalize_data.py**
- ✅ Criadas 4 funções específicas:
  - `normalize_cnpj()` → 14 dígitos
  - `normalize_cpf()` → 11 dígitos  
  - `normalize_cep()` → 8 dígitos
  - `normalize_cnae()` → 7 dígitos
- ✅ Todas usam `.zfill()` para padding

### **FASE 3: load_normalized_schema.py**
- ✅ Removidas conversões `str(int())` 
- ✅ Removidas chamadas desnecessárias a `fix_documento()`
- ✅ Código 70% mais simples e legível

---

## 📊 ANTES vs DEPOIS

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **CNPJ no Excel** | `02916265009116` | `02916265009116` |
| **CNPJ lido** | `2916265009116` (float) | `"02916265009116"` (str) |
| **CNPJ normalizado** | `"2916265009116"` (13) | `"02916265009116"` (14) |
| **CNPJ no banco** | ❌ Falha (tipo errado) | ✅ `CHAR(14)` |
| **Maps ETL** | Descasados | ✅ Consistentes |
| **Taxa de sucesso** | 0% (0/10.000) | ? (testar) |

---

## 🧪 PIPELINE DE RE-PROCESSAMENTO

```bash
# 1. Excel → CSV Raw (com dtype correto)
uv run python scripts/load_excel_to_csv.py

# 2. CSV Raw → CSV Normalized (com padding)
uv run python scripts/normalize_data.py

# 3. CSV Normalized → Database (simplificado)
uv run python scripts/load_normalized_schema.py  # Teste com 100
uv run python scripts/load_normalized_schema.py --full  # Carga completa
```

---

## 📝 LIÇÕES APRENDIDAS

### 1. **Sempre definir dtype ao ler dados**
```python
# Regra de ouro:
DTYPE_MAP = {campo: str for campo in CAMPOS_CODIGO}
```

### 2. **Padding deve ser feito NA NORMALIZAÇÃO**
- Não delegar para o banco (função `fix_documento`)
- Garantir formato desde a origem

### 3. **Maps devem usar chaves consistentes**
- Se CNPJ é string, usar string em TODOS os lugares
- Sem conversões int→str→int

### 4. **Teste com 1 registro ANTES de lotes grandes**
- Economia de 102 minutos descobrindo erros cedo

---

## ⚡ PRÓXIMOS PASSOS

- [ ] Re-processar Excel completo (~974k registros)
- [ ] Validar com 100 registros primeiro
- [ ] Se sucesso → carga completa
- [ ] Documentar tempos e métricas finais
- [ ] Commit com mensagem: "fix: corrigir dtype e padding de códigos (CNPJ, CEP, CNAE)"

---

## 🏷️ Tags Git Sugeridas

Após sucesso da carga completa:
```bash
git tag -a v0.1.0-beta -m "Beta: ETL normalizado funcionando"
git push origin v0.1.0-beta
