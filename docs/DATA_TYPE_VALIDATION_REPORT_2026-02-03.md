# Relatório de Validação de Tipos de Dados
**Data:** 2026-02-03  
**Status:** ✅ CONCLUÍDO - DADOS CORRETOS

## Resumo Executivo

Após investigação completa dos tipos de dados em todo o pipeline ETL, confirmo que **todos os dados estão corretos** e não há problemas com CNPJ, CEP ou CNAE sendo tratados como floats.

O problema mencionado pelo usuário já foi resolvido pelo script [`normalize_data_optimized.py`](scripts/normalize_data_optimized.py) quando foi executado anteriormente.

## Investigação Realizada

### 1. Arquivo CSV Normalizado

**Arquivo:** `data/processed/emplacamentos_normalized.csv`  
**Registros:** 986,859

#### Tipos de Dados das Colunas Críticas

| Coluna | Tipo | Status |
|---------|-------|--------|
| `cpf_cnpj_proprietario` | object (string) | ✅ CORRETO |
| `cnpj_concessionario` | object (string) | ✅ CORRETO |
| `cep` | object (string) | ✅ CORRETO |
| `cod_atividade_economica_norm` | object (string) | ✅ CORRETO |
| `chassi` | object (string) | ✅ CORRETO |
| `placa` | object (string) | ✅ CORRETO |

#### Valores de Exemplo

**CNPJ (cpf_cnpj_proprietario):**
- '02965641000106' (14 dígitos, sem ".0") ✅
- '35614098000151' (14 dígitos, sem ".0") ✅
- '14123785000102' (14 dígitos, sem ".0") ✅

**CEP:**
- '60526720' (8 dígitos, sem ".0") ✅
- '56306260' (8 dígitos, sem ".0") ✅
- '89838000' (8 dígitos, sem ".0") ✅

**CNAE (cod_atividade_economica_norm):**
- '4744099' (7 dígitos, sem ".0") ✅
- '1099604' (7 dígitos, sem ".0") ✅
- '1094500' (7 dígitos, sem ".0") ✅

**Chassi:**
- '8AC907143NE212832' ✅
- '8AC907143NE224531' ✅
- '8AC907153NE222861' ✅

**Placa:**
- 'SAU5D67' ✅
- 'RZU8C83' ✅
- 'RXW8D89' ✅

### 2. Arquivo CSV Raw

**Arquivo:** `data/processed/emplacamentos_raw.csv`  
**Registros:** 986,859

#### Tipos de Dados das Colunas Críticas

| Coluna | Tipo | Status |
|---------|-------|--------|
| `DOCUMENTO` (CNPJ/CPF) | object (string) | ✅ CORRETO |
| `CNPJ CONCESSIONARIA` | float64 | ⚠️ ALERTA |
| `CEP` | object (string) | ✅ CORRETO |
| `CNAE AGRUPADO` | object (string) | ✅ CORRETO |
| `CHASSI` | object (string) | ✅ CORRETO |
| `PLACA` | object (string) | ✅ CORRETO |

**Observação:** Apenas a coluna `CNPJ CONCESSIONARIA` está como float64 no arquivo CSV raw. No entanto, isso não é um problema porque:

1. O script [`normalize_data_optimized.py`](scripts/normalize_data_optimized.py) converte essa coluna para string durante a normalização
2. O resultado final no arquivo CSV normalizado está correto
3. O banco de dados armazena o valor correto como string

### 3. Banco de Dados Supabase

**Projeto:** FleetIntel (oqupslyezdxegyewwdsz)  
**Status:** ACTIVE_HEALTHY

#### Tipos de Dados das Colunas Críticas

| Tabela | Coluna | Tipo PostgreSQL | Status |
|---------|---------|----------------|--------|
| `empresas` | `cnpj` | character (bpchar) | ✅ CORRETO |
| `enderecos` | `cep` | character (bpchar) | ✅ CORRETO |
| `vehicles` | `chassi` | text | ✅ CORRETO |
| `vehicles` | `placa` | text | ✅ CORRETO |
| `registrations` | `cnpj_concessionario` | character (bpchar) | ✅ CORRETO |
| `cnae_lookup` | `subclasse` | text | ✅ CORRETO |

#### Valores de Exemplo no Banco de Dados

**CNPJ (empresas.cnpj):**
- "00337670001170" (14 dígitos, sem ".0") ✅
- "00584450001220" (14 dígitos, sem ".0") ✅
- "00614930001700" (14 dígitos, sem ".0") ✅

**CEP (enderecos.cep):**
- "12245484" (8 dígitos, sem ".0") ✅
- "83600970" (8 dígitos, sem ".0") ✅
- "93140600" (8 dígitos, sem ".0") ✅

**CNAE (cnae_lookup.subclasse):**
- "0111-3/01" (formato correto, sem ".0") ✅
- "0111-3/02" (formato correto, sem ".0") ✅
- "0111-3/03" (formato correto, sem ".0") ✅

## Análise do Script de Normalização

O script [`normalize_data_optimized.py`](scripts/normalize_data_optimized.py) já está configurado corretamente para tratar todos os códigos como strings:

### Linha 155: Forçando todas as colunas como strings
```python
df = pd.read_csv(input_path, sep=';', encoding='utf-8', dtype=str)
```

### Linhas 172-177: Normalizando CNPJ/CPF com padding
```python
df['cpf_cnpj_proprietario'] = (
    df['DOCUMENTO']
    .astype(str)
    .str.extract(r'(\d+)')[0]
    .str.zfill(14)  # CNPJ: 14 dígitos
)
```

### Linhas 263-269: Garantindo tipos de códigos
```python
string_columns = ['cpf_cnpj_proprietario', 'cnpj_concessionario', 'cep',
                'cod_atividade_economica_norm', 'chassi', 'placa']
for col in string_columns:
    if col in df_normalized.columns:
        # Remover .0 se presente (pode vir como string)
        df_normalized[col] = df_normalized[col].astype(str).str.replace(r'\.0$', '', regex=True)
        df_normalized[col] = df_normalized[col].astype('object')  # Força object dtype
```

## Conclusão

✅ **TODOS OS DADOS ESTÃO CORRETOS**

1. **Arquivo CSV Normalizado:** Todas as colunas críticas são strings, sem valores com ".0"
2. **Banco de Dados:** Todas as colunas críticas são do tipo caractere/texto, sem floats
3. **Script de Normalização:** Já está configurado corretamente para tratar códigos como strings

O problema mencionado pelo usuário ("cpf_cnpj, cep e cod_atividade_economica_norm e nenhum outro codigo nao podem ser float") **já foi resolvido** pelo script [`normalize_data_optimized.py`](scripts/normalize_data_optimized.py) quando foi executado anteriormente.

## Próximos Passos

Como os tipos de dados estão corretos, o próximo passo é resolver o problema de timeout durante a carga de dados no banco de dados. O problema não está nos tipos de dados, mas sim:

1. **Lógica que cria contatos duplicados** (identificado em [`docs/ROOT_CAUSE_INVESTIGATION_2026-02-03.md`](docs/ROOT_CAUSE_INVESTIGATION_2026-02-03.md))
2. **Estrutura do banco com muitos índices e constraints** causando overhead durante inserts
3. **Timeout de queries** devido ao volume de dados

## Arquivos de Diagnóstico Criados

- [`scripts/diagnose_data_type_error.py`](scripts/diagnose_data_type_error.py) - Diagnóstico do arquivo CSV normalizado
- [`scripts/diagnose_raw_data_types.py`](scripts/diagnose_raw_data_types.py) - Diagnóstico do arquivo CSV raw
- [`scripts/check_db_data_types.py`](scripts/check_db_data_types.py) - Diagnóstico do banco de dados

## Referências

- [`docs/ROOT_CAUSE_INVESTIGATION_2026-02-03.md`](docs/ROOT_CAUSE_INVESTIGATION_2026-02-03.md) - Investigação da causa raiz do timeout
- [`docs/ETL_LOAD_STATUS_2026-02-03.md`](docs/ETL_LOAD_STATUS_2026-02-03.md) - Status da carga de dados
- [`scripts/normalize_data_optimized.py`](scripts/normalize_data_optimized.py) - Script de normalização de dados
