ESTRATÉGIA DE BRANCHES:

1. main - branch de produção
   - Sempre estável e deployável
   - Só recebe merges via Pull Request de 'dev'
   - Protegida: requer aprovação e CI passing

2. dev - branch de homologação/staging
   - Ambiente de testes integrados
   - Recebe merges de feature branches
   - Base para criar novas features

3. feature/* - branches de desenvolvimento
   - Padrão: feature/GT-XX-descricao-curta
   - Exemplos: 
     * feature/GT-11-fastapi-setup
     * feature/GT-16-langgraph-agent
   - Criar sempre a partir de 'dev'
   - Deletar após merge

4. hotfix/* - correções urgentes
   - Padrão: hotfix/descricao-problema
   - Criar a partir de 'main'
   - Merge em 'main' E 'dev'

FLUXO DE TRABALHO:
1. Puxar dev: git checkout dev && git pull
2. Criar feature: git checkout -b feature/GT-XX-nome
3. Desenvolver e commitar
4. Push: git push -u origin feature/GT-XX-nome
5. Abrir PR para 'dev'
6. Após aprovação, merge em 'dev'
7. Testar em staging
8. PR de 'dev' para 'main' quando estável
