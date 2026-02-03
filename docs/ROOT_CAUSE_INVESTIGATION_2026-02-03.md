# Relatório de Investigação da Causa Raiz do Timeout
**Data:** 2026-02-03  
**Horário:** 00:59 UTC

## Resumo Executivo

A investigação revelou que **o problema não é apenas de timeout**, mas sim de **estrutura dos dados e arquitetura do banco de dados**. A carga teve sucesso parcial (2,6% dos dados), mas há problemas estruturais que impedem a conclusão completa.

## Descobertas Principais

### 1. Discrepância na Tabela Contatos

**Estatísticas dos Arrays:**
- Média telefones: 2.40 elementos
- Média celulares: 1.82 elementos
- Máximo telefones: 5 elementos
- Máximo celulares: 2 elementos
- **Nenhum registro com arrays grandes (>10 elementos)**

**Problema Identificado:**
- Tabela contatos: **5.666 registros**
- Script preparou: **155.622 contatos**
- Discrepância: **99.822 contatos a mais**

**Análise:**
A discrepância MASSIVA indica que o script está preparando contatos incorretamente. Possíveis causas:
1. O script está criando um registro de contato para CADA registro de empresa, mesmo quando a empresa já tem contato
2. O script está duplicando contatos devido a problemas com a lógica de agrupamento
3. O script está incluindo contatos de empresas que não deveriam ter contato

### 2. Discrepância na Tabela Registrations

**Estatísticas:**
- Tabela registrations: **9.443 registros**
- Script preparou: **919.941 registros**
- Discrepância: **66.918 registros a mais**
- Registros pulados: **66.918 (7,3%)**

**Análise:**
A discrepância indica que 66.918 registros foram pulados, provavelmente devido a:
1. Empresa_id ausente (empresa não encontrada no banco)
2. Vehicle_id ausente (veículo não encontrado no banco)
3. Problemas com os dados normalizados

### 3. Estrutura da Tabela Contatos

**Colunas:**
- id: integer (NOT NULL)
- empresa_id: integer (NOT NULL)
- telefones: ARRAY (nullable)
- celulares: ARRAY (nullable)
- email: text (nullable)
- created_at: timestamp with time zone (nullable)
- updated_at: timestamp with time zone (nullable)

**Índices:**
- contatos_pkey (PRIMARY KEY)
- contatos_empresa_id_key (UNIQUE)
- idx_contatos_empresa
- idx_contatos_telefones_gin (GIN index para arrays)

**Triggers:**
- update_contatos_updated_at: UPDATE

**Constraints:**
- contatos_empresa_id_fkey: FOREIGN KEY
- contatos_empresa_id_key: UNIQUE
- contatos_pkey: PRIMARY KEY
- CHECK constraints

**Problemas Identificados:**
1. **Índice GIN em arrays**: O índice `idx_contatos_telefones_gin` pode estar causando problemas de performance durante inserts
2. **Trigger de UPDATE**: O trigger `update_contatos_updated_at` pode estar causando overhead desnecessário
3. **Muitos índices**: 4 índices em uma tabela pequena podem causar overhead durante inserts

### 4. Estrutura da Tabela Registrations

**Colunas:**
- id: integer (NOT NULL)
- external_id: text (NOT NULL)
- vehicle_id: integer (NOT NULL)
- empresa_id: integer (NOT NULL)
- data_emplacamento: date (NOT NULL)
- municipio_emplacamento: text (nullable)
- uf_emplacamento: character (nullable)
- regiao_emplacamento: text (nullable)
- cnpj_concessionario: character (nullable)
- concessionario: text (nullable)
- area_operacional: text (nullable)
- preco: numeric (nullable)
- preco_validado: boolean (nullable)
- fonte: text (nullable)
- versao_carga: integer (nullable)
- created_at: timestamp with time zone (nullable)

**Índices:**
- registrations_pkey (PRIMARY KEY)
- registrations_external_id_key (UNIQUE)
- registrations_vehicle_id_data_emplacamento_key (UNIQUE)
- idx_registrations_external_id
- idx_registrations_vehicle
- idx_registrations_empresa
- idx_registrations_data_emplacamento
- idx_registrations_uf_emplacamento
- idx_registrations_preco

**Constraints:**
- registrations_empresa_id_fkey: FOREIGN KEY
- registrations_external_id_key: UNIQUE
- registrations_pkey: PRIMARY KEY
- registrations_vehicle_id_data_emplacamento_key: UNIQUE
- registrations_vehicle_id_fkey: FOREIGN KEY
- 5 CHECK constraints

**Problemas Identificados:**
1. **Muitos índices**: 9 índices em uma tabela podem causar overhead significativo durante inserts
2. **2 UNIQUE constraints**: Constraints UNIQUE podem causar overhead durante inserts
3. **2 FOREIGN KEY constraints**: Constraints FOREIGN KEY podem causar overhead durante inserts
4. **5 CHECK constraints**: Constraints CHECK podem causar overhead durante inserts
5. **Índice GIN em external_id**: O índice `idx_registrations_external_id` pode estar causando problemas de performance

## Causa Raiz do Problema

### Problema 1: Dados Inconsistentes

**Descrição:**
O script está preparando 155.622 contatos, mas a tabela contatos tem apenas 5.666 registros. Isso indica que o script está criando contatos duplicados ou incorretamente.

**Causa Provável:**
1. O script está criando um registro de contato para CADA registro de empresa, mesmo quando a empresa já tem contato
2. O script está duplicando contatos devido a problemas com a lógica de agrupamento
3. O script está incluindo contatos de empresas que não deveriam ter contato

**Impacto:**
- Discrepância de 99.822 contatos
- Tempo de processamento desnecessário
- Uso de memória desnecessário
- Possível deadlock na tabela contatos

### Problema 2: Arquitetura do Banco de Dados

**Descrição:**
As tabelas contatos e registrations têm muitos índices e constraints, o que pode estar causando overhead significativo durante inserts.

**Causa Provável:**
1. Muitos índices em tabelas grandes
2. Índices GIN em arrays podem causar overhead durante inserts
3. Triggers de UPDATE podem causar overhead desnecessário
4. Constraints UNIQUE e FOREIGN KEY podem causar overhead durante inserts

**Impacto:**
- Timeout durante inserts
- Performance degradada
- Uso excessivo de recursos do banco de dados

## Recomendações

### 1. Corrigir a Lógica de Preparação de Contatos

**Ação:**
Revisar a lógica de preparação de contatos no script `load_normalized_schema_optimized_v2.py` para garantir que:
1. Cada empresa tenha apenas UM registro de contato
2. Contatos não sejam duplicados
3. Apenas empresas com dados de contato tenham registros de contato

**Código a Revisar:**
```python
# Função load_empresas_enderecos_contatos() no script
# Verificar se a lógica está criando contatos duplicados
```

### 2. Otimizar a Estrutura do Banco de Dados

**Ação 1: Remover Índices Desnecessários**
- Remover índices GIN em arrays durante inserts
- Remover índices que não são usados frequentemente
- Recriar índices APÓS a carga de dados

**Ação 2: Remover Triggers Desnecessários**
- Remover o trigger `update_contatos_updated_at` se não for necessário
- Avaliar se o trigger está causando overhead significativo

**Ação 3: Simplificar Constraints**
- Avaliar se todas as constraints são necessárias
- Considerar remover constraints CHECK que não são críticas
- Considerar remover constraints UNIQUE que podem ser substituídas por lógica de aplicação

### 3. Melhorar o Script de Carga

**Ação 1: Implementar Retry Automático**
- Implementar retry automático em caso de erro de conexão
- Implementar rollback automático em caso de erro
- Implementar checkpoint para retomar de onde parou

**Ação 2: Implementar Validação de Dados**
- Validar se empresa_id existe antes de criar contato
- Validar se vehicle_id existe antes de criar registration
- Validar se os dados estão consistentes antes de inserir

**Ação 3: Implementar Logging Detalhado**
- Implementar logging detalhado de erros
- Implementar logging de progresso
- Implementar logging de performance

### 4. Aumentar Timeout e Otimizar Performance

**Ação 1: Aumentar Timeout**
- Aumentar timeout de 30 minutos para 60 minutos
- Considerar aumentar para 120 minutos se necessário

**Ação 2: Reduzir Batch Size**
- Reduzir batch size de 500 para 250
- Considerar reduzir para 100 se ainda houver timeout

**Ação 3: Implementar Parallel Inserts**
- Considerar implementar inserts paralelos em múltiplas conexões
- Avaliar se o Supabase suporta inserts paralelos

## Próximos Passos

### Imediato (Hoje)
1. Revisar a lógica de preparação de contatos no script
2. Corrigir a discrepância de 99.822 contatos
3. Reexecutar o script de carga com as correções

### Curto Prazo (Esta Semana)
1. Otimizar a estrutura do banco de dados
2. Remover índices e triggers desnecessários
3. Implementar retry automático e validação de dados
4. Reexecutar a carga completa de dados

### Médio Prazo (Próxima Semana)
1. Implementar inserts paralelos
2. Implementar logging detalhado
3. Implementar checkpoint para retomar de onde parou
4. Validar integridade dos dados

## Conclusão

O problema de timeout não é apenas um problema de configuração, mas sim um problema estrutural com:
1. **Dados inconsistentes** (discrepância de 99.822 contatos)
2. **Arquitetura do banco de dados** (muitos índices e constraints)
3. **Lógica de preparação de dados** (criando contatos duplicados)

Para resolver o problema, é necessário:
1. Corrigir a lógica de preparação de contatos
2. Otimizar a estrutura do banco de dados
3. Implementar retry automático e validação de dados
4. Aumentar timeout e otimizar performance

Apenas resolver os sintomas (aumentar timeout, reduzir batch size) não vai resolver a causa raiz do problema.
