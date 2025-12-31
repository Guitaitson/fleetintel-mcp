# Variáveis de Ambiente - FleetIntel MCP

## Padrão de Nomenclatura
Todas as variáveis usam `SCREAMING_SNAKE_CASE` (letras maiúsculas com underscores).

## Uso do .env.example
1. Copie o arquivo `.env.example` para:
   - `.env.local` (ambiente local)
   - `.env.staging` (ambiente de staging)
   - `.env.production` (ambiente de produção)
2. Preencha os valores necessários em cada arquivo
3. O sistema carregará automaticamente as variáveis baseado no valor de `ENVIRONMENT`

## Ambientes Suportados
- `local`: Desenvolvimento local
- `staging`: Homologação/pré-produção
- `production`: Produção (dados reais)

## Variáveis Obrigatórias vs Opcionais
| Variável               | Obrigatória | Descrição                                                                 |
|------------------------|-------------|---------------------------------------------------------------------------|
| `ENVIRONMENT`          | Sim         | Define o ambiente de execução (local, staging, production)               |
| `FLEET_API_BASE_URL`   | Sim         | URL base da API externa de frota                                          |
| `FLEET_API_KEY`        | Sim         | Chave de autenticação da API de frota                                    |
| `SUPABASE_URL`         | Sim         | URL do projeto Supabase                                                   |
| `SUPABASE_ANON_KEY`    | Sim         | Chave pública para operações client-side                                  |
| `SUPABASE_SERVICE_ROLE_KEY` | Sim    | Chave privilegiada para operações server-side (armazenar com segurança)  |
| `REDIS_HOST`           | Sim         | Endereço do servidor Redis                                                |
| `API_SECRET_KEY`       | Sim         | Chave secreta para JWT/sessions (gerar com: `openssl rand -hex 32`)      |
| `ALLOWED_USERS`        | Sim         | Números de telefone permitidos no MVP (separados por vírgula)             |

Variáveis marcadas como **opcionais** possuem valores padrão que podem ser mantidos ou modificados conforme necessidade.

## Boas Práticas
- Nunca commit arquivos `.env` no Git
- Mantenha chaves sensíveis em gerenciadores de secrets (Infisical, AWS Secrets Manager)
- Revise periodicamente as permissões das chaves de API
