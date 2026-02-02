# Recomendações para Resolver Timeout do Supabase

**Data**: 2026-02-02 16:30 BRT  
**Projeto**: FleetIntel MCP  
**Prioridade**: ALTA

---

## 📋 Resumo do Problema

**Problema**: Timeout ao executar INSERT com ON CONFLICT na tabela `marcas`

**Erro**: `asyncpg.exceptions.QueryCanceledError: canceling statement due to statement timeout`

**Contexto**:
- Timeout ocorre na inserção de apenas 19 marcas
- Mesmo INSERT funciona quando executado isoladamente
- Timeout configurado para 5 minutos (300.000ms)
- Não há políticas de RLS na tabela (array vazio)

---

## 🔍 Análise das Causas Possíveis

### 1. Timeout Muito Restrito do Supabase
**Descrição**: O plano gratuito do Supabase pode ter um timeout muito restrito para operações de escrita.

**Sintomas**:
- Timeouts em operações simples (INSERT de 19 registros)
- Mesmo com timeout de 5 minutos, a operação falha

**Investigação Necessária**:
- Verificar configurações de timeout no painel do Supabase
- Comparar com outros projetos Supabase
- Considerar upgrade para plano com mais recursos

### 2. Lock na Tabela
**Descrição**: Pode haver uma transação em andamento bloqueando a tabela.

**Sintomas**:
- Timeout consistente em múltiplas tentativas
- Operações simples funcionam isoladamente

**Investigação Necessária**:
- Verificar se há transações em andamento
- Verificar locks ativos na tabela
- Verificar se há conexões ativas ao banco

### 3. ON CONFLICT Causando Overhead
**Descrição**: A cláusula ON CONFLICT pode causar overhead significativo em tabelas grandes.

**Sintomas**:
- Timeout ocorre especificamente com ON CONFLICT
- INSERT sem ON CONFLICT funciona isoladamente

**Análise**:
- ON CONFLICT requer verificação de constraint antes de inserir
- Em tabelas grandes, essa verificação pode ser demorada
- O overhead pode ser significativo em operações de batch

---

## ✅ Soluções Imediatas

### Solução 1: Usar INSERT sem ON CONFLICT
**Descrição**: Remover a cláusula ON CONFLICT para a primeira inserção.

**Implementação**:
```python
# Em load_normalized_schema_optimized_v2.py, função load_marcas_modelos:
stmt = text("""
    INSERT INTO marcas (nome)
    VALUES (:nome)
""")
params = [{"nome": marca} for marca in marcas_unicas]
await conn.execute(stmt, params)
```

**Vantagens**:
- Mais rápido (sem verificação de constraint)
- Menos complexo
- Funciona isoladamente

**Desvantagens**:
- Pode causar duplicatas se executado múltiplas vezes
- Precisa de estratégia para evitar duplicatas

### Solução 2: Aumentar Timeout do Supabase
**Descrição**: Aumentar o timeout do banco de dados.

**Implementação**:
```python
# Em load_normalized_schema_optimized_v2.py:
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"server_settings": {"statement_timeout": "600000"}}  # 10 minutos
)
```

**Vantagens**:
- Mais tempo para operações complexas
- Reduz chance de timeout

**Desvantagens**:
- Pode mascarar problemas de performance reais
- Não resolve a causa raiz se for lock

### Solução 3: Usar COPY Command
**Descrição**: Usar o comando COPY do PostgreSQL para cargas muito grandes.

**Implementação**:
```python
# Criar arquivo temporário CSV para marcas
import csv
import io

# Criar CSV em memória
output = io.StringIO()
writer = csv.writer(output)
writer.writerow(['nome'])
for marca in marcas_unicas:
    writer.writerow([marca])

# Usar COPY
await conn.execute(text("COPY marcas (nome) FROM STDIN WITH (FORMAT CSV)"))
await conn.connection.connection.copy_expert.copy(
    output.getvalue().encode('utf-8'),
    sep=',',
    null='',
)
```

**Vantagens**:
- Muito mais rápido que INSERT (10-100x)
- Menos overhead de rede
- Melhor para grandes volumes

**Desvantagens**:
- Mais complexo de implementar
- Requer gerenciamento de arquivos temporários

### Solução 4: Implementar Upsert com MERGE
**Descrição**: Usar INSERT ... ON CONFLICT DO UPDATE SET ... ao invés de DO NOTHING.

**Implementação**:
```python
stmt = text("""
    INSERT INTO marcas (nome)
    VALUES (:nome)
    ON CONFLICT (nome) DO UPDATE SET
        nome = EXCLUDED.nome,
        updated_at = NOW()
""")
```

**Vantagens**:
- Atualiza registros existentes
- Evita duplicatas
- Mais robusto que DO NOTHING

**Desvantagens**:
- Mais complexo
- Pode causar mais overhead

---

## 🎯 Plano de Ação

### Imediato (Hoje)

1. **Implementar Solução 1** (Recomendada):
   - Remover ON CONFLICT da primeira inserção
   - Testar com 100 registros
   - Validar que funciona

2. **Testar com Timeout Aumentado**:
   - Aumentar timeout para 10 minutos
   - Testar com 10.000 registros
   - Validar que resolve o problema

3. **Se Timeout Persistir**:
   - Implementar Solução 3 (COPY command)
   - Testar com 10.000 registros
   - Validar performance

4. **Investigar Supabase**:
   - Entrar em contato com suporte do Supabase
   - Verificar logs do banco
   - Verificar configurações de timeout
   - Comparar com outros projetos

### Curto Prazo (Esta Semana)

1. **Validar Solução Escolhida**:
   - Executar carga completa com solução implementada
   - Medir tempo total
   - Validar integridade dos dados

2. **Documentar Resultados**:
   - Atualizar PROJECT_STATUS.md
   - Criar relatório final de ETL
   - Documentar lições aprendidas

3. **Continuar Desenvolvimento**:
   - Implementar FastAPI MCP Server (GT-11 a GT-15)
   - Criar endpoints básicos de consulta
   - Configurar CI/CD básico

---

## 📊 Checklist de Validação

### Antes de Implementar Solução
- [ ] Testar INSERT sem ON CONFLICT
- [ ] Validar que funciona com 100 registros
- [ ] Testar com timeout aumentado (10 minutos)
- [ ] Validar que resolve o problema

### Após Implementar Solução
- [ ] Executar carga completa de 974k registros
- [ ] Medir tempo total de execução
- [ ] Validar integridade dos dados
- [ ] Comparar com projeção (~38 minutos)
- [ ] Documentar resultados finais

---

## 📝 Conclusão

O problema de timeout do Supabase está bloqueando a carga completa do ETL. As soluções apresentadas neste documento devem ser testadas sistematicamente, começando pela mais simples (remover ON CONFLICT) e progredindo para soluções mais robustas (COPY command) se necessário.

Enquanto o problema de timeout é investigado, o desenvolvimento do FastAPI MCP Server pode continuar em paralelo, garantindo que o projeto avance mesmo com essa limitação.

---

**Documento criado por**: Kilo Code Agent  
**Data de criação**: 2026-02-02 16:30 BRT  
**Versão**: 1.0
