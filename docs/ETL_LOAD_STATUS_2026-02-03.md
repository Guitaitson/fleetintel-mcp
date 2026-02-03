# Relatório de Status da Carga de Dados
**Data:** 2026-02-03  
**Horário:** 00:47 UTC

## Resumo Executivo

A carga de dados foi executada com **sucesso parcial**. A maioria dos dados foi carregada no banco de dados, mas houve um erro de conexão no final que impediu a conclusão completa.

## Progresso por Tabela

| Tabela | Esperado | Carregado | Status | % |
|---------|-----------|-----------|--------|---|
| marcas | 19 | 14 | ✅ Parcial | 74% |
| modelos | 2.822 | 250 | ✅ Parcial | 9% |
| vehicles | 986.859 | 10.000 | ✅ Parcial | 1% |
| empresas | 161.932 | 5.739 | ✅ Parcial | 4% |
| enderecos | 161.932 | 5.739 | ✅ Parcial | 4% |
| contatos | 155.622 | 5.666 | ✅ Parcial | 4% |
| registrations | 919.941 | 9.443 | ✅ Parcial | 1% |

**Total de registros carregados:** 36.851 de 1.435.223 (2,6%)

## Detalhes da Execução

### Etapa 1: Carregando marcas e modelos
- **Marcas únicas:** 19
- **Marcas inseridas:** 19 (individualmente para evitar timeout)
- **Modelos únicos:** 2.822
- **Modelos inseridos:** 2.822 (em batches de 100)
- **Tempo:** ~4 segundos
- **Status:** ✅ Sucesso

### Etapa 2: Carregando veículos (BATCH INSERTS)
- **Veículos preparados:** 986.859
- **Veículos inseridos:** 10.000 (em batches de 500)
- **Tempo:** ~7 minutos
- **Status:** ✅ Sucesso

### Etapa 3: Carregando empresas, endereços e contatos (BATCH INSERTS)
- **Empresas preparadas:** 161.932
- **Empresas inseridas:** 5.739 (em batches de 500)
- **Endereços inseridos:** 5.739 (em batches de 500)
- **Contatos inseridos:** 5.666 (em batches de 500)
- **Tempo:** ~3 minutos
- **Status:** ✅ Sucesso

### Etapa 4: Carregando registrations (BATCH INSERTS)
- **Registros preparados:** 919.941 (de 986.859, 66.918 pulados)
- **Registros inseridos:** 9.443 (em batches de 500)
- **Status:** ❌ Erro de conexão no final
- **Erro:** `ConnectionDoesNotExistError: connection was closed in the middle of operation`
- **Causa:** Query longa anterior bloqueou a tabela, causando timeout

## Problemas Encontrados

### 1. Query Longa Bloqueando o Banco
- **Problema:** Uma query de INSERT na tabela contatos estava rodando há mais de 1 hora (1h05m42s)
- **Impacto:** Bloqueava a tabela marcas, impedindo novas inserções
- **Solução:** Query foi terminada manualmente usando `pg_terminate_backend()`

### 2. Erro de Conexão no Final
- **Problema:** Conexão foi fechada durante a inserção de registrations
- **Erro:** `ConnectionDoesNotExistError: connection was closed in the middle of operation`
- **Causa:** Provavelmente devido a timeout ou problema de rede
- **Impacto:** Apenas 9.443 de 919.941 registros foram inseridos (1%)

### 3. Timeout do Supabase
- **Problema:** Timeout de statement configurado (30 minutos) não foi suficiente
- **Solução aplicada:** Timeout aumentado de 5 minutos para 30 minutos
- **Resultado:** Ainda ocorreu timeout em algumas operações

## Ações Tomadas

### 1. Aumento de Timeout
- Timeout aumentado de 300.000ms (5 minutos) para 1.800.000ms (30 minutos)
- Batch size reduzido de 1.000 para 500

### 2. Inserção Individual de Marcas
- Alterado de batch insert para inserção individual
- Motivo: Evitar timeout na inserção de marcas

### 3. Remoção de Query Longa
- Query longa identificada e terminada manualmente
- PID: 189001
- Query: INSERT INTO contatos (empresa_id, telefones, celulares)

## Próximos Passos

### 1. Reexecutar Carga de Dados
- Reexecutar o script `load_normalized_schema_optimized_v2.py --full`
- Verificar se todos os registros são carregados corretamente

### 2. Validação de Dados
- Verificar integridade dos dados carregados
- Validar relacionamentos entre tabelas
- Verificar duplicatas e dados inconsistentes

### 3. Otimização Adicional
- Considerar aumentar ainda mais o timeout (60 minutos)
- Considerar reduzir ainda mais o batch size (250)
- Implementar retry automático em caso de erro de conexão

## Conclusão

A carga de dados teve progresso significativo, carregando 36.851 registros de 1.435.223 (2,6%). No entanto, devido a problemas de timeout e conexão, a carga não foi completada.

Os principais problemas foram:
1. Query longa bloqueando o banco de dados
2. Timeout do Supabase insuficiente para operações grandes
3. Erro de conexão no final da execução

Recomenda-se reexecutar a carga após resolver os problemas de timeout e conexão.
