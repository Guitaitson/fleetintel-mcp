# Scripts do Projeto

Scripts utilitários para ETL, banco de dados e manutenção.

## Estrutura

```
scripts/
├── *.py                    # Scripts ativos (ver abaixo)
├── *.sh                    # Scripts Shell (Docker)
├── *.sql                   # Scripts SQL
└── README.md               # Este arquivo
```

## Scripts Ativos

### ETL (Carga de Dados)

| Script | Descrição | Uso |
|--------|-----------|-----|
| `load_excel_to_csv_optimized.py` | Excel → CSV Raw | `uv run python scripts/load_excel_to_csv_optimized.py` |
| `normalize_data_optimized.py` | CSV Raw → CSV Normalized | `uv run python scripts/normalize_data_optimized.py` |
| `load_normalized_schema_optimized_v7.py` | CSV → PostgreSQL | `uv run python scripts/load_normalized_schema_optimized_v7.py` |
| `clean_database.py` | Limpa dados do banco | `uv run python scripts/clean_database.py` |

### Database (Banco de Dados)

| Script | Descrição | Uso |
|--------|-----------|-----|
| `apply_migrations.py` | Aplica migrations | `uv run python scripts/apply_migrations.py` |
| `validate_migrations.py` | Valida migrations | `uv run python scripts/validate_migrations.py` |
| `db_health.py` | Verifica saúde do DB | `uv run python scripts/db_health.py` |
| `migrate.py` | Migração de dados | `uv run python scripts/migrate.py` |

### Utilitários

| Script | Descrição | Uso |
|--------|-----------|-----|
| `validate_env.py` | Valida variáveis de ambiente | `uv run python scripts/validate_env.py` |
| `test_connection.py` | Testa conexão DB | `uv run python scripts/test_connection.py` |
| `validate_csv_structure.py` | Valida estrutura CSV | `uv run python scripts/validate_csv_structure.py` |
| `validate_source_files.py` | Valida arquivos fonte | `uv run python scripts/validate_source_files.py` |

## Comandos Essenciais

```bash
# Configurar ambiente
uv venv
.venv\Scripts\activate
uv pip install -r requirements.txt

# ETL Pipeline (ordem correta)
uv run python scripts/load_excel_to_csv_optimized.py      # Excel → CSV Raw
uv run python scripts/normalize_data_optimized.py        # CSV Raw → CSV Normalized
uv run python scripts/load_normalized_schema_v7.py       # CSV → PostgreSQL

# Testes
uv run python scripts/test_connection.py                   # Testar conexão Supabase
uv run python scripts/validate_env.py                     # Validar variáveis de ambiente
```

## Scripts Arquivados

Arquivos obsoletos, duplicados ou temporários foram movidos para `.archive/`.

Para recuperar um arquivo do archive:
```bash
git restore .archive/scripts/<arquivo> scripts/<arquivo>
```

## Licença

MIT
