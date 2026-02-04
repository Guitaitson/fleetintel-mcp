# Relatório de Validação de Dados Inseridos

**Data:** 2026-02-04
**Status:** CRÍTICO - Problemas de integridade encontrados

## Resumo Executivo

O processo de carga ETL está em execução há aproximadamente 1 hora e 11 minutos, com progresso de 19% na etapa de veículos (3,679 de 19,738 batches). O tempo estimado para conclusão é de aproximadamente 4 horas apenas para a etapa de veículos.

Foram identificados **problemas críticos de integridade dos dados** que tornam os dados inseridos inúteis para o negócio.

## Dados Inseridos

| Tabela | Registros | Status |
|---------|-----------|--------|
| marcas | 23 | ✓ |
| modelos | 250 | ✓ |
| vehicles | 10,000 | ⚠️ (sem modelo) |
| empresas | 5,739 | ✓ |
| enderecos | 5,739 | ✓ |
| contatos | 5,666 | ✓ |
| registrations | 9,443 | ✓ |

## Problemas Críticos Identificados

### 1. Veículos sem Modelo (CRÍTICO)

**Impacto:** 10,000 de 10,000 veículos (100%) não têm modelo associado

**Causa Raiz:**
- Erros durante a inserção dos modelos (batches 29-37)
- Mensagem de erro: "This result object does not return rows. It has been closed automatically"
- O `modelo_map` não foi preenchido corretamente devido aos erros
- Quando os veículos são inseridos, o `modelo_id` é NULL porque o modelo não existe no mapa

**Consequência:**
- Dados de veículos são inúteis sem modelo
- Impossível realizar consultas por modelo
- Dados incompletos para análise de frota

### 2. Empresas sem Contato (MODERADO)

**Impacto:** 73 de 5,739 empresas (1.27%) não têm contato

**Causa:**
- Algumas empresas no CSV não têm informações de contato
- O script não está criando contatos para essas empresas

**Consequência:**
- Dificuldade em entrar em contato com essas empresas
- Dados incompletos para lead scoring

## Schema da Tabela Vehicles

```
Colunas da tabela vehicles:
  id                   | integer              | NOT NULL
  chassi               | text                 | NOT NULL
  placa                | text                 | NULL
  marca_id             | integer              | NULL
  modelo_id            | integer              | NULL  ← PROBLEMA: está NULL para todos os veículos
  ano_fabricacao       | integer              | NULL
  ano_modelo           | integer              | NULL
  cor                  | text                 | NULL
  categoria            | text                 | NULL
  marca_nome           | text                 | NULL
  modelo_nome          | text                 | NULL
  created_at           | timestamp with time zone | NULL
  updated_at           | timestamp with time zone | NULL
```

## Validação de Integridade

| Verificação | Resultado | Status |
|-------------|-----------|--------|
| Veículos sem marca | 0 | ✓ |
| Veículos sem modelo | 10,000 | ✗ CRÍTICO |
| Empresas sem endereço | 0 | ✓ |
| Empresas sem contato | 73 | ⚠️ |
| Registros sem veículo | 0 | ✓ |
| Registros sem empresa | 0 | ✓ |

## Análise de Performance

### Tempo Estimado por Etapa

| Etapa | Batches | Tempo por Batch | Tempo Total |
|--------|----------|----------------|-------------|
| Marcas | 19 | ~2s | ~38s |
| Modelos | 38 | ~52s | ~33min |
| Veículos | 19,738 | ~1s | ~5.5h |
| Empresas | ~115 | ~1s | ~2min |
| Endereços | ~115 | ~1s | ~2min |
| Contatos | ~115 | ~1s | ~2min |
| Registros | ~19,000 | ~1s | ~5.3h |

**Tempo Total Estimado:** ~11.5 horas

### Problemas de Performance

1. **Batch Size Muito Pequeno:** batch_size=50 resulta em 19,738 batches para veículos
2. **Delay Entre Batches:** 0.1s de delay adiciona ~33 minutos ao tempo total
3. **Pool Size Reduzido:** pool_size=5 limita o número de conexões simultâneas
4. **Max Concurrent Batches:** max_concurrent_batches=3 limita o paralelismo

## Causa Raiz dos Erros de Modelo

O erro "This result object does not return rows. It has been closed automatically" ocorre quando:

1. O script tenta usar `RETURNING id, marca_id, nome` em uma transação aninhada
2. O resultado é fechado automaticamente antes de poder ler as linhas
3. O `modelo_map` não é preenchido corretamente
4. Quando os veículos são inseridos, o `modelo_id` é NULL

## Recomendações

### Imediatas (PARAR PROCESSO ATUAL)

1. **Parar o processo de carga atual** - Os dados estão incompletos e inúteis
2. **Limpar os dados inseridos** - Remover veículos sem modelo
3. **Corrigir o script de carga** - Resolver o problema do `RETURNING` em transações aninhadas

### Curto Prazo (NOVA ABORDAGEM)

1. **Aumentar batch_size:** De 50 para 500 ou 1000
2. **Remover delay entre batches:** Eliminar o delay de 0.1s
3. **Aumentar pool_size:** De 5 para 10 ou 20
4. **Aumentar max_concurrent_batches:** De 3 para 10 ou 20
5. **Corrigir inserção de modelos:** Usar uma abordagem diferente para evitar o erro do `RETURNING`

### Médio Prazo (VALIDAÇÃO)

1. **Adicionar validação após cada etapa:** Verificar integridade dos dados antes de continuar
2. **Adicionar checkpoint mais frequente:** Salvar progresso a cada 100 registros em vez de 1000
3. **Adicionar rollback automático:** Se houver erro em uma etapa, fazer rollback de toda a etapa

### Longo Prazo (OTIMIZAÇÃO)

1. **Usar COPY do PostgreSQL:** Em vez de INSERT, usar COPY para carga em massa
2. **Desabilitar índices temporariamente:** Remover índices antes da carga e recriar depois
3. **Usar transações maiores:** Em vez de transações separadas por batch, usar uma transação por etapa

## Próximos Passos

1. [ ] Parar o processo de carga atual
2. [ ] Limpar os dados inseridos (veículos sem modelo)
3. [ ] Corrigir o script de carga para resolver o problema do `RETURNING`
4. [ ] Testar o script corrigido com um pequeno conjunto de dados
5. [ ] Executar a carga completa com o script corrigido
6. [ ] Validar a integridade dos dados após a carga
7. [ ] Gerar relatório de qualidade dos dados

## Conclusão

O processo de carga atual está **lento e produzindo dados incompletos**. É necessário parar o processo, corrigir os problemas identificados e executar uma nova carga com uma abordagem otimizada.

**Status:** CRÍTICO - Ação imediata necessária
