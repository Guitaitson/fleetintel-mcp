# Plano de Correção e Otimização do ETL

**Data:** 2026-02-04
**Status:** PRONTO PARA IMPLEMENTAÇÃO

## Resumo Executivo

O processo de carga ETL atual está lento (~11.5 horas) e produzindo dados incompletos (veículos sem modelo). Este documento apresenta um plano detalhado para corrigir os problemas identificados e otimizar significativamente a performance.

## Problemas Identificados

### 1. Veículos sem Modelo (CRÍTICO)

**Impacto:** 10,000 de 10,000 veículos (100%) não têm modelo associado

**Causa Raiz:**
- Erros durante a inserção dos modelos (batches 29-37)
- Mensagem de erro: "This result object does not return rows. It has been closed automatically"
- O script usa `RETURNING id, marca_id, nome` em uma transação aninhada (`begin_nested()`)
- O resultado é fechado automaticamente antes de poder ler as linhas
- O `modelo_map` não é preenchido corretamente devido aos erros
- Quando os veículos são inseridos, o `modelo_id` é NULL porque o modelo não existe no mapa

**Consequência:**
- Dados de veículos são inúteis sem modelo
- Impossível realizar consultas por modelo
- Dados incompletos para análise de frota

### 2. Performance Muito Lenta

**Tempo Estimado:** ~11.5 horas para carga completa

**Causas:**
1. **batch_size muito pequeno:** batch_size=50 resulta em 19,738 batches para veículos
2. **Delay entre batches:** 0.1s de delay adiciona ~33 minutos ao tempo total
3. **pool_size reduzido:** pool_size=5 limita o número de conexões simultâneas
4. **max_concurrent_batches pequeno:** max_concurrent_batches=3 limita o paralelismo

**Consequência:**
- Processo muito lento
- Computador ocupado por muitas horas
- Risco de interrupção durante a noite

### 3. Falta de Validação Durante o Processo

**Causa:**
- Não há validação de integridade após cada etapa
- O checkpoint só salva progresso, não valida dados
- Problemas só são descobertos no final do processo

**Consequência:**
- Dados incompletos podem não ser detectados a tempo
- Perda de tempo se precisar reexecutar

## Solução Proposta

### 1. Corrigir Problema de Modelos (CRÍTICO)

**Abordagem:** Separar inserção de modelos em duas etapas

**Etapa 1: Inserir Modelos sem RETURNING**
```python
# Inserir todos os modelos sem usar RETURNING
for batch in batches:
    async with conn.begin():
        await conn.execute(
            text("""
                INSERT INTO modelos (marca_id, nome)
                VALUES (:marca_id, :nome)
                ON CONFLICT (marca_id, nome) DO UPDATE SET
                    nome = EXCLUDED.nome
            """),
            batch
        )
```

**Etapa 2: Buscar IDs dos Modelos Inseridos**
```python
# Depois de inserir todos os modelos, buscar os IDs
result = await conn.execute(
    text("""
        SELECT id, marca_id, nome FROM modelos
        WHERE (marca_id, nome) = ANY(:modelos)
    """),
    {"modelos": [(m['marca_id'], m['nome']) for m in modelo_data]}
)
rows = result.fetchall()
for row in rows:
    modelo_id, marca_id, nome = row
    modelo_map[(marca_id, nome)] = modelo_id
```

**Benefícios:**
- Evita o erro "result object does not return rows"
- Garante que o `modelo_map` seja preenchido corretamente
- Todos os veículos terão modelo associado

### 2. Otimizar Performance

**Parâmetros Atuais:**
- batch_size: 50
- pool_size: 5
- max_concurrent_batches: 3
- batch_delay: 0.1s

**Novos Parâmetros:**
- batch_size: 1000 (20x maior)
- pool_size: 20 (4x maior)
- max_concurrent_batches: 20 (6.7x maior)
- batch_delay: 0s (removido)

**Impacto na Performance:**

| Etapa | Batches Atuais | Tempo por Batch | Tempo Total | Batches Novos | Tempo por Batch | Tempo Total |
|--------|----------------|----------------|-------------|----------------|----------------|-------------|
| Marcas | 19 | ~2s | ~38s | 1 | ~2s | ~2s |
| Modelos | 38 | ~52s | ~33min | 2 | ~52s | ~2min |
| Veículos | 19,738 | ~1s | ~5.5h | 987 | ~1s | ~17min |
| Empresas | ~115 | ~1s | ~2min | 6 | ~1s | ~6s |
| Endereços | ~115 | ~1s | ~2min | 6 | ~1s | ~6s |
| Contatos | ~115 | ~1s | ~2min | 6 | ~1s | ~6s |
| Registros | ~19,000 | ~1s | ~5.3h | 987 | ~1s | ~17min |
| **TOTAL** | - | - | **~11.5h** | - | - | **~40min** |

**Melhoria:** Redução de ~94% no tempo total (de 11.5h para 40min)

### 3. Adicionar Validação de Integridade

**Validação Após Cada Etapa:**
```python
async def validate_after_step(conn, step_name):
    """Valida integridade dos dados após cada etapa."""
    print(f"\nValidando integridade após {step_name}...")
    
    # Verificar contagens esperadas vs reais
    # Verificar integridade de referências
    # Verificar tipos de dados
    # Verificar valores nulos inesperados
```

**Validação Final:**
```python
async def validate_final(conn):
    """Validação completa após todas as etapas."""
    print("\nValidação final dos dados...")
    
    # Verificar todas as tabelas
    # Verificar integridade referencial
    # Verificar tipos de dados
    # Gerar relatório de qualidade
```

**Benefícios:**
- Detecta problemas a tempo
- Evita reexecução desnecessária
- Garante qualidade dos dados

## Plano de Implementação

### Fase 1: Preparação (5 min)
- [ ] Parar processo de carga atual
- [ ] Limpar dados incompletos (veículos sem modelo)
- [ ] Fazer backup do estado atual do banco

### Fase 2: Criar Script v7 (15 min)
- [ ] Criar `scripts/load_normalized_schema_optimized_v7.py`
- [ ] Implementar correção do problema de modelos (duas etapas)
- [ ] Atualizar parâmetros de performance:
  - batch_size: 50 → 1000
  - pool_size: 5 → 20
  - max_concurrent_batches: 3 → 20
  - batch_delay: 0.1s → 0s
- [ ] Adicionar validação após cada etapa
- [ ] Adicionar validação final completa

### Fase 3: Testar Script v7 (10 min)
- [ ] Testar com 100 registros (TEST_MODE=True)
- [ ] Validar que todos os veículos têm modelo
- [ ] Validar integridade dos dados
- [ ] Verificar performance (deve ser muito mais rápido)

### Fase 4: Executar Carga Completa (40 min)
- [ ] Limpar banco de dados (remover dados incompletos)
- [ ] Executar carga completa com script v7
- [ ] Monitorar progresso
- [ ] Validar integridade após cada etapa

### Fase 5: Validação Final (10 min)
- [ ] Executar validação completa dos dados
- [ ] Verificar contagens de todas as tabelas
- [ ] Verificar integridade referencial
- [ ] Verificar tipos de dados
- [ ] Gerar relatório de qualidade

### Fase 6: Documentação (5 min)
- [ ] Atualizar `docs/PROJECT_STATUS.md`
- [ ] Criar relatório de qualidade dos dados
- [ ] Commitar e pushar resultados

**Tempo Total Estimado:** ~1.5 horas

## Detalhes da Implementação

### Correção do Problema de Modelos

**Arquivo:** `scripts/load_normalized_schema_optimized_v7.py`

**Mudanças na função `load_models`:**

```python
async def load_models(conn, df: pd.DataFrame, marca_map: Dict[str, int]) -> Dict[tuple, int]:
    """Carrega modelos no banco de dados."""
    print("\nEtapa 1: Carregando modelos...")
    
    # Preparar dados dos modelos
    print("Preparando modelos...")
    modelo_data = []
    for _, row in modelos.iterrows():
        marca_nome = row['marca']
        modelo_nome = row['modelo']
        if pd.notna(marca_nome) and pd.notna(modelo_nome):
            marca_id = marca_map.get(marca_nome)
            if marca_id:
                modelo_data.append({
                    'marca_id': marca_id,
                    'nome': modelo_nome
                })
    
    print(f"   {len(modelo_data)} modelos preparados")
    
    # Inserir modelos SEM usar RETURNING
    modelo_map = {}
    from tqdm import tqdm
    
    BATCH_SIZE = 1000  # Aumentado de 50 para 1000
    
    for i in tqdm(range(0, len(modelo_data), BATCH_SIZE), desc="   Inserindo modelos (batch)"):
        batch = modelo_data[i:i+BATCH_SIZE]
        try:
            # Usar transação separada (não aninhada)
            async with conn.begin():
                await conn.execute(
                    text("""
                        INSERT INTO modelos (marca_id, nome)
                        VALUES (:marca_id, :nome)
                        ON CONFLICT (marca_id, nome) DO UPDATE SET
                            nome = EXCLUDED.nome
                    """),
                    batch
                )
        except Exception as e:
            print(f"\n   Erro no batch {i//BATCH_SIZE}: {e}")
            # Inserir individualmente em caso de erro
            for item in batch:
                try:
                    async with conn.begin():
                        await conn.execute(
                            text("""
                                INSERT INTO modelos (marca_id, nome)
                                VALUES (:marca_id, :nome)
                                ON CONFLICT (marca_id, nome) DO UPDATE SET
                                    nome = EXCLUDED.nome
                            """),
                            item
                        )
                except Exception as e2:
                    print(f"   Erro ao inserir modelo {item}: {e2}")
    
    # Buscar IDs dos modelos inseridos
    print("Buscando IDs dos modelos inseridos...")
    result = await conn.execute(
        text("""
            SELECT id, marca_id, nome FROM modelos
        """)
    )
    rows = result.fetchall()
    for row in rows:
        modelo_id, marca_id, nome = row
        modelo_map[(marca_id, nome)] = modelo_id
    
    print(f"   {len(modelo_map)} modelos inseridos")
    return marca_map, modelo_map
```

### Otimização de Performance

**Parâmetros Atualizados:**
```python
# Parâmetros de performance
BATCH_SIZE = 1000  # Aumentado de 50 para 1000
POOL_SIZE = 20  # Aumentado de 5 para 20
MAX_CONCURRENT_BATCHES = 20  # Aumentado de 3 para 20
BATCH_DELAY = 0  # Removido (era 0.1s)
```

### Validação de Integridade

**Função de Validação:**
```python
async def validate_integrity(conn, step_name):
    """Valida integridade dos dados após uma etapa."""
    print(f"\nValidando integridade após {step_name}...")
    
    # Verificar contagens
    if step_name == "modelos":
        result = await conn.execute(text("SELECT COUNT(*) FROM modelos"))
        count = result.scalar()
        print(f"   Total de modelos: {count:,}")
        
        # Verificar modelos sem marca
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM modelos m
            LEFT JOIN marcas ma ON m.marca_id = ma.id
            WHERE ma.id IS NULL
        """))
        count = result.scalar()
        if count > 0:
            print(f"   ⚠️  Modelos sem marca: {count:,}")
        else:
            print(f"   ✓ Todos os modelos têm marca")
    
    elif step_name == "veiculos":
        result = await conn.execute(text("SELECT COUNT(*) FROM vehicles"))
        count = result.scalar()
        print(f"   Total de veículos: {count:,}")
        
        # Verificar veículos sem modelo
        result = await conn.execute(text("""
            SELECT COUNT(*) FROM vehicles v
            LEFT JOIN modelos m ON v.modelo_id = m.id
            WHERE m.id IS NULL
        """))
        count = result.scalar()
        if count > 0:
            print(f"   ✗ Veículos sem modelo: {count:,}")
        else:
            print(f"   ✓ Todos os veículos têm modelo")
```

## Riscos e Mitigações

### Risco 1: Timeout Durante a Carga

**Probabilidade:** Baixa
**Impacto:** Alto
**Mitigação:**
- Usar checkpoint a cada 1000 registros
- Implementar retry automático com exponential backoff
- Monitorar progresso continuamente

### Risco 2: Erro de Memória

**Probabilidade:** Baixa
**Impacto:** Médio
**Mitigação:**
- Usar batch_size de 1000 (não muito grande)
- Implementar garbage collection entre batches
- Monitorar uso de memória

### Risco 3: Conflito de Dados

**Probabilidade:** Média
**Impacto:** Baixo
**Mitigação:**
- Usar ON CONFLICT DO UPDATE em todas as inserções
- Validar dados antes de inserir
- Implementar rollback em caso de erro

## Critérios de Sucesso

O processo será considerado bem-sucedido quando:

1. **Integridade dos Dados:**
   - ✓ Todos os veículos têm modelo associado
   - ✓ Todas as empresas têm endereço
   - ✓ Todas as empresas têm contato (quando disponível)
   - ✓ Todos os registros têm veículo e empresa

2. **Performance:**
   - ✓ Tempo total < 1 hora
   - ✓ Sem erros de timeout
   - ✓ Sem erros de memória

3. **Qualidade dos Dados:**
   - ✓ Tipos de dados corretos
   - ✓ Sem valores nulos inesperados
   - ✓ Sem duplicatas

## Próximos Passos

1. [ ] Parar processo de carga atual
2. [ ] Limpar dados incompletos
3. [ ] Criar script v7 com correções
4. [ ] Testar script v7 com 100 registros
5. [ ] Executar carga completa com script v7
6. [ ] Validar integridade dos dados
7. [ ] Gerar relatório de qualidade
8. [ ] Documentar resultados

## Conclusão

O plano proposto resolve todos os problemas identificados:

1. **Corrige o problema crítico** de veículos sem modelo
2. **Otimiza significativamente a performance** (redução de 94% no tempo)
3. **Adiciona validação contínua** para detectar problemas a tempo
4. **Permite testar bastante** antes de executar a carga completa

Com essas correções, o processo de carga será rápido, confiável e produzirá dados de alta qualidade.

**Status:** PRONTO PARA IMPLEMENTAÇÃO NO MODO CODE
