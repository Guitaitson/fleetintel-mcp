# Lições Aprendidas e Melhores Práticas - FleetIntel MCP

**Data**: 2026-02-02 16:24 BRT  
**Projeto**: FleetIntel MCP  
**Versão**: 1.0

---

## 📋 Propósito

Este documento documenta as lições aprendidas, decisões técnicas e melhores práticas estabelecidas durante o desenvolvimento do projeto FleetIntel MCP. O objetivo é manter o conhecimento organizado e facilitar a continuidade do desenvolvimento, independentemente da ferramenta de IA utilizada.

---

## 🎯 Princípios Fundamentais

### 1. Documentação é Primeira Classe
- **Regra**: Toda decisão técnica, mudança de arquitetura ou lição aprendida deve ser documentada
- **Onde**: `docs/` para documentação técnica, `docs/git/` para decisões de Git
- **Por que**: Permite que qualquer ferramenta de IA entenda o contexto e continue o trabalho
- **Como**: Criar arquivos markdown com explicações claras e exemplos de código

### 2. Sincronização com Git é Obrigatória
- **Regra**: Todo trabalho significativo deve ser commitado e pushado para o GitHub
- **Por que**: Garante que o contexto esteja sempre atualizado e disponível
- **Quando**: Ao final de cada sessão de trabalho, antes de trocar de ferramenta
- **Como**: 
  ```bash
  git add .
  git commit -m "tipo: descrição concisa"
  git push origin main
  ```

### 3. Conventional Commits
- **Regra**: Usar Conventional Commits para todas as mensagens de commit
- **Tipos**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- **Exemplos**:
  - `feat: implementar batch inserts no ETL`
  - `fix: corrigir timeout de conexão com Supabase`
  - `docs: adicionar lições aprendidas ao projeto`
  - `refactor: otimizar queries de banco de dados`

### 4. Branches Estruturados
- **Regra**: Usar branches estruturados para diferentes tipos de trabalho
- **Tipos**:
  - `feature/` - Novas funcionalidades
  - `bugfix/` - Correção de bugs
  - `hotfix/` - Correções urgentes em produção
  - `refactor/` - Refatoração de código
- **Exemplo**: `feature/etl-optimization-batch-inserts`

---

## 📚 Lições Aprendidas

### Lição 1: Performance do ETL é Crítica
**Problema**: Carga completa de 974k registros levaria 40+ dias (0.3 reg/s)

**Causa Raiz**: 1.1M queries individuais (row-by-row inserts)

**Solução Implementada**:
- Batch inserts (1000 registros por batch)
- Vectorized operations (Pandas C-level)
- Connection pooling (15 → 50 conexões)
- Temporary indexes (removidos devido a timeout)

**Resultado**: 423 reg/s (1.410x mais rápido)

**Lições**:
1. Performance deve ser considerada desde o início do projeto
2. Testes de carga devem ser feitos com volumes representativos
3. Otimizações de banco de dados são essenciais para grandes volumes

### Lição 2: Timeout de Banco de Dados
**Problema**: Timeout ao executar INSERT com ON CONFLICT na tabela `marcas`

**Causa Possível**:
- Timeout muito restrito do Supabase
- Lock na tabela devido a RLS (Row Level Security)
- ON CONFLICT causando verificação de constraint demorada

**Tentativas de Solução**:
1. ✅ Aumentar timeout para 5 minutos (300.000ms)
2. ✅ Reduzir batch size de 1000 para 100
3. ✅ Remover índices temporários
4. ✅ Simplificar código para sempre usar ON CONFLICT

**Status**: ❌ Timeout persiste

**Lições**:
1. Timeout do banco deve ser configurado adequadamente para o volume de dados
2. ON CONFLICT pode causar overhead significativo em tabelas grandes
3. Índices temporários podem causar timeout em tabelas já grandes
4. Considerar usar COPY command para cargas muito grandes

### Lição 3: Codificação de Caracteres
**Problema**: Erro de codificação Unicode no script original

**Causa**: Caractere Unicode (emoji ou caractere especial) não pode ser codificado em cp1252 (encoding padrão do Windows)

**Solução**: Remover caracteres Unicode problemáticos

**Lições**:
1. Evitar emojis em código Python (especialmente em print statements)
2. Usar encoding UTF-8 explicitamente quando necessário
3. Testar scripts em diferentes ambientes (Windows/Linux/Mac)
4. Considerar usar f-strings para evitar problemas de codificação

### Lição 4: Testes Progressivos
**Problema**: Testes iniciais com 100 registros não revelaram problemas de escala

**Solução Implementada**:
- Teste 1: 100 registros (98 inseridos em 8s)
- Teste 2: 10.000 registros (9.443 inseridos em 22s)

**Lições**:
1. Testes devem ser progressivos: 100 → 1k → 10k → 100k → completo
2. Medir performance em cada etapa para identificar gargalos
3. Validar integridade dos dados após cada teste
4. Documentar resultados de todos os testes

### Lição 5: Documentação de Status
**Problema**: Falta de documentação clara sobre o estado atual do projeto

**Solução Implementada**:
- [`PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) - Status geral do projeto
- [`STATUS_REPORT_2026-02-02.md`](docs/STATUS_REPORT_2026-02-02.md) - Relatório inicial
- [`STATUS_REPORT_2026-02-02_V2.md`](docs/STATUS_REPORT_2026-02-02_V2.md) - Relatório atualizado

**Lições**:
1. Documentação de status deve ser atualizada regularmente
2. Relatórios devem incluir: problemas encontrados, soluções tentadas, próximos passos
3. Manter histórico de relatórios para rastrear evolução
4. Status deve refletir o estado real, não o ideal

---

## 🏗 Melhores Práticas

### 1. Estrutura de Documentação

```
docs/
├── PROJECT_STATUS.md              # Status geral do projeto (ATUALIZAR SEMPRE)
├── LESSONS_LEARNED.md         # Este arquivo (LIÇÕES APRENDIDAS)
├── git/
│   ├── branching-strategy.md   # Estratégia de branches
│   ├── tagging-strategy.md      # Estratégia de versionamento
│   └── rollback-guide.md        # Guia de rollback
├── setup/
│   ├── environment-variables.md  # Variáveis de ambiente
│   └── SUPABASE_SETUP.md      # Setup do Supabase
└── policies/
    ├── cache-policy.md          # Política de cache
    ├── mvp-checklist.md         # Checklist de MVP
    ├── mvp-scope.md            # Escopo do MVP
    ├── query-guardrails.md      # Guardrails de queries
    └── user-management.md       # Gestão de usuários
```

### 2. Estrutura de Scripts

```
scripts/
├── load_normalized_schema_optimized_v2.py  # Script otimizado (USAR ESTE)
├── normalize_data_optimized.py              # Normalização vectorizada
├── load_excel_to_csv_optimized.py        # Excel → CSV com chunking
├── benchmark_etl.py                       # Benchmark de performance
├── README_OPTIMIZED.md                    # Documentação dos scripts otimizados
├── test_connection.py                      # Teste de conexão
├── test_etl_one_record.py              # Teste ETL com 1 registro
├── check_db_counts.py                    # Verificar contagem do banco
└── test_marcas_insert.py                # Teste específico de marcas
```

### 3. Estrutura de Código

```
app/                    # FastAPI application (MCP Server)
├── core/
│   └── config.py      # Configuração central
└── schemas/
    └── query_schemas.py  # Schemas de validação

agent/                  # LangGraph agent code
├── __init__.py
└── README.md

mcp/                     # MCP server code
├── main.py
├── scheduler.py
└── jobs/
    └── incremental_sync.py

mcp_server/              # MCP server (alternative)
├── __init__.py
└── README.md

src/                     # Source code
├── config/
│   └── settings.py
└── fleet_intel_mcp/
    ├── config.py
    └── db/
        └── connection.py
```

### 4. Convenções de Código

#### Python
- **PEP 8**: Seguir PEP 8 para formatação e estilo
- **Type Hints**: Obrigatório para todas as funções e classes
- **Docstrings**: Google-style docstrings para todas as funções públicas
- **Nomes**: `snake_case` para funções/variáveis, `PascalCase` para classes
- **Imports**: Agrupar imports em 3 blocos: stdlib, third-party, local

#### SQL
- **Keywords em UPPERCASE**: SELECT, INSERT, UPDATE, DELETE, etc.
- **Nomes de tabelas em snake_case**: `marcas`, `modelos`, `vehicles`
- **Nomes de colunas em snake_case**: `chassi`, `placa`, `ano_fabricacao`
- **Indentação**: 2 espaços para melhor legibilidade

#### Git
- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- **Branches**: `feature/`, `bugfix/`, `hotfix/`, `refactor/`
- **Mensagens**: Descrição concisa no imperativo (ex: "implementar batch inserts")

### 5. Regras de Negócio

#### CNPJ, CPF, CEP, CNAE
- **Sempre strings**: Nunca tratar como números
- **Padding de zeros**: Usar `zfill()` para garantir tamanho correto
  - CNPJ: 14 dígitos
  - CPF: 11 dígitos
  - CEP: 8 dígitos
  - CNAE: 7 dígitos

#### Dados Sensíveis
- **Nunca no Git**: `.env`, `data/` com dados reais
- **Proteção**: `.gitignore` deve proteger arquivos sensíveis
- **Logs**: Remover credenciais e dados PII antes de commitar

#### ETL Pipeline
- **Idempotência**: Re-executar não duplica dados (usa upserts)
- **Validação**: Validar dados em cada etapa do pipeline
- **Rollback**: Capacidade de rollback em caso de erro

### 6. Testes

#### Tipos de Testes
1. **Unit Tests**: Testar funções individuais
2. **Integration Tests**: Testar integração entre componentes
3. **E2E Tests**: Testar fluxo completo de ponta a ponta
4. **Performance Tests**: Medir e validar performance

#### Estratégia de Testes
- **Testes Progressivos**: 100 → 1k → 10k → 100k → completo
- **Testes de Carga**: Validar com volumes representativos
- **Testes de Regressão**: Garantir que mudanças não quebram funcionalidades existentes

### 7. Performance

#### Métricas Importantes
- **Taxa de Processamento**: Registros por segundo
- **Tempo Total**: Tempo total de execução
- **Uso de Memória**: Pico de memória durante execução
- **Queries Executadas**: Número total de queries ao banco

#### Otimizações de Banco de Dados
- **Índices**: Criar índices nas colunas usadas em WHERE e JOIN
- **Batch Inserts**: Agrupar INSERTs em batches
- **Connection Pooling**: Reutilizar conexões
- **Prepared Statements**: Reutilizar statements preparados
- **COPY Command**: Usar COPY para cargas muito grandes

### 8. Monitoramento e Logging

#### Níveis de Log
- **DEBUG**: Informações detalhadas para debugging
- **INFO**: Informações gerais sobre progresso
- **WARNING**: Avisos sobre problemas potenciais
- **ERROR**: Erros que requerem atenção

#### Práticas de Logging
- **Progress Bars**: Usar `tqdm` para operações longas
- **Structured Logging**: Usar logging estruturado em produção
- **Error Handling**: Capturar e logar erros com contexto

### 9. Segurança

#### Autenticação e Autorização
- **Environment Variables**: Nunca commitar `.env`
- **API Keys**: Usar variáveis de ambiente para chaves de API
- **RLS (Row Level Security**: Implementar políticas de acesso no nível de linha

#### Validação de Dados
- **Input Validation**: Validar todos os inputs antes de processar
- **SQL Injection**: Usar parameterized queries (nunca concatenar strings)
- **XSS**: Sanitizar outputs HTML/JSON

### 10. Deploy e Produção

#### Checklist de Deploy
- [ ] Testes completos e passando
- [ ] Documentação atualizada
- [ ] Variáveis de ambiente configuradas
- [ ] Migrations aplicadas
- [ ] Backup realizado
- [ ] Monitoramento configurado

#### Estratégia de Rollback
- **Hotfixes**: Branches `hotfix/` para correções urgentes
- **Versionamento**: Usar Semantic Versioning (MAJOR.MINOR.PATCH)
- **Rollback**: Capacidade de reverter para versão anterior se necessário

---

## 🔄 Workflow de Troca de Ferramenta

### Antes de Trocar (Cline → KiloCode/Cursor/etc.)

1. **Commitar Mudanças**:
   ```bash
   git add .
   git commit -m "tipo: descrição concisa"
   ```

2. **Atualizar Documentação**:
   - Atualizar `docs/PROJECT_STATUS.md` com progresso
   - Adicionar lições aprendidas a `docs/LESSONS_LEARNED.md`
   - Documentar problemas encontrados e soluções

3. **Push para GitHub**:
   ```bash
   git push origin main
   ```

4. **Criar Issue no GitHub** (opcional):
   - Criar issue para rastrear trabalho pendente
   - Incluir contexto e próximos passos

### Na Nova Ferramenta

1. **Pull Últimas Mudanças**:
   ```bash
   git pull origin main
   ```

2. **Ler Documentação em Ordem**:
   1. `docs/LESSONS_LEARNED.md` (este arquivo)
   2. `docs/PROJECT_STATUS.md` (estado atual)
   3. `.clinerules` (regras do projeto)
   4. `docs/ONBOARDING_AGENT.md` (guia para agentes)

3. **Verificar Ambiente**:
   - Dependências instaladas (`uv pip list`)
   - Variáveis de ambiente (`.env`)
   - Conexões funcionando (`python scripts/test_connection.py`)

4. **Continuar Trabalho**:
   - Ler issues abertas no GitHub
   - Continuar de onde parou
   - Fazer perguntas se necessário

---

## 📊 Checklist de Qualidade

### Antes de Commitar
- [ ] Código segue PEP 8?
- [ ] Type hints presentes?
- [ ] Docstrings completas?
- [ ] Testes passando?
- [ ] Documentação atualizada?
- [ ] Sem prints de debug?
- [ ] Sem hardcoded values?
- [ ] Tratamento de erros adequado?

### Antes de Push
- [ ] Branch atual está sincronizada?
- [ ] Commits seguem Conventional Commits?
- [ ] Mensagens de commit são claras?
- [ ] Documentação atualizada no commit?
- [ ] Sem segredos no código?
- [ ] `.gitignore` está correto?

---

## 🎓 Histórico de Versões

### v1.0 (2026-02-02)
- Inicialização do projeto
- Setup de ambiente
- Database redesign V2
- ETL V2 implementado
- Epic 0-3 concluído

### v1.1 (2026-02-02 - Planejado)
- Epic 4: ETL V2 - Correções de Tipos de Dados
- Epic 5: ETL Performance Optimization (em progresso)
- Otimizações implementadas (batch inserts, vectorized operations)
- Testes validados (100 e 10.000 registros)
- Documentação criada (lições aprendidas, melhores práticas)

---

## 📞 Suporte e Recursos

### Documentação Externa
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Pandas](https://pandas.pydata.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Supabase](https://supabase.com/docs)
- [LangGraph](https://langchain-ai.github.io/langgraph/)

### Documentação Interna
- [`PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)
- [`ONBOARDING_AGENT.md`](docs/ONBOARDING_AGENT.md)
- [`.clinerules`](.clinerules)
- [`README.md`](README.md)

---

## ✅ Conclusão

Este documento serve como guia de referência para o desenvolvimento contínuo do projeto FleetIntel MCP. As lições aprendidas e melhores práticas aqui documentadas devem ser aplicadas e atualizadas conforme o projeto evolui.

**Próxima Atualização**: Após resolver o problema de timeout do Supabase e completar a carga ETL

---

**Documento criado por**: Kilo Code Agent  
**Data de criação**: 2026-02-02 16:24 BRT  
**Versão**: 1.0
