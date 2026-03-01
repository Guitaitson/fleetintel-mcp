#!/usr/bin/env python3
"""
FleetIntel MCP — Rotina de Sincronização Incremental via API de Dados

Busca novos emplacamentos de veículos pesados e atualiza o banco PostgreSQL
local via upsert idempotente (chassi + data_emplacamento como chave natural).

Modos de uso:
    python scripts/sync_from_api.py --mode incremental          # últimos 7 dias (padrão)
    python scripts/sync_from_api.py --mode incremental --days 3 # últimos N dias
    python scripts/sync_from_api.py --mode full --date-range 2024-01-01:2024-03-31
    python scripts/sync_from_api.py --dry-run                   # simula sem gravar

Variáveis de ambiente requeridas:
    HUBQUEST_API_KEY   — chave de autenticação da API (header `key`)
    DATABASE_URL       — postgresql://user:pass@host:port/dbname

Boas práticas (conforme documentação da API):
    - Para atualização diária: usar date_type=atualizacao com últimos 5-7 dias
    - Para backfill histórico: usar date_type=emplacamento com janela de 90 dias
    - API entra em cold-start após inatividade — warm-up automático é executado
"""

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
import psycopg2
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Setup de logging
# ---------------------------------------------------------------------------

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("fleetintel.sync")

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

load_dotenv()

API_KEY = os.getenv("HUBQUEST_API_KEY", "")
API_BASE_URL = os.getenv("HUBQUEST_API_URL", "https://api.hub-quest.com/dados")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Limites e timeouts
PAGE_SIZE = 1000           # máximo permitido pela API
MAX_RETRIES = 3            # tentativas por página em caso de falha
RETRY_BACKOFF = 5          # segundos de espera entre retries
WARMUP_TIMEOUT = 60        # timeout para a chamada de warm-up (API em cold-start)
REQUEST_TIMEOUT = 30       # timeout para chamadas normais
COMMIT_EVERY_N = 500       # commit a cada N registros inseridos


@dataclass
class SyncStats:
    """Estatísticas de execução do sync."""
    pages_fetched: int = 0
    records_fetched: int = 0
    vehicles_upserted: int = 0
    empresas_upserted: int = 0
    registrations_upserted: int = 0
    errors: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)

    def elapsed_seconds(self) -> float:
        return (datetime.utcnow() - self.started_at).total_seconds()

    def rate(self) -> float:
        elapsed = self.elapsed_seconds()
        return self.records_fetched / elapsed if elapsed > 0 else 0

    def summary(self) -> str:
        return (
            f"Páginas: {self.pages_fetched} | "
            f"Registros: {self.records_fetched} | "
            f"Veículos: {self.vehicles_upserted} | "
            f"Empresas: {self.empresas_upserted} | "
            f"Emplacamentos: {self.registrations_upserted} | "
            f"Erros: {self.errors} | "
            f"Tempo: {self.elapsed_seconds():.1f}s | "
            f"Taxa: {self.rate():.1f} reg/s"
        )


# ---------------------------------------------------------------------------
# Conexão com banco
# ---------------------------------------------------------------------------

def get_db_connection():
    """Cria conexão psycopg2 a partir da DATABASE_URL."""
    import re
    url = DATABASE_URL
    # Suporta postgresql+asyncpg:// (SQLAlchemy) e postgresql:// (psycopg2)
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    match = re.match(r"postgresql://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)", url)
    if not match:
        raise ValueError(f"DATABASE_URL inválida: {url[:30]}...")
    user, password, host, port, dbname = match.groups()
    return psycopg2.connect(
        host=host,
        port=int(port or 5432),
        dbname=dbname,
        user=user,
        password=password,
        connect_timeout=10,
    )


# ---------------------------------------------------------------------------
# Cliente da API
# ---------------------------------------------------------------------------

def build_api_params(
    date_range: str,
    date_type: str,
    page: int,
    limit: int = PAGE_SIZE,
) -> dict:
    return {
        "date_range": date_range,
        "date_type": date_type,
        "page": page,
        "limit": limit,
    }


def warmup_api(client: httpx.Client) -> bool:
    """
    Executa warm-up da API (pode estar em cold-start).
    A documentação avisa que as primeiras requisições do dia são mais lentas.
    """
    log.info("Executando warm-up da API (cold-start)...")
    try:
        resp = client.get(
            API_BASE_URL,
            params={"date_range": "1", "date_type": "emplacamento", "page": 0, "limit": 1},
            timeout=WARMUP_TIMEOUT,
        )
        if resp.status_code == 200:
            log.info("Warm-up concluído com sucesso.")
            return True
        log.warning(f"Warm-up retornou status {resp.status_code}.")
        return False
    except httpx.TimeoutException:
        log.warning("Warm-up timeout — API pode estar em cold-start. Continuando...")
        return False
    except Exception as e:
        log.warning(f"Warm-up falhou: {e}")
        return False


def fetch_page(
    client: httpx.Client,
    date_range: str,
    date_type: str,
    page: int,
    stats: SyncStats,
) -> Optional[dict]:
    """Busca uma página da API com retry automático."""
    params = build_api_params(date_range=date_range, date_type=date_type, page=page)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.get(API_BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            # API retorna {} para páginas inválidas/vazias
            if not data or not data.get("results"):
                return None

            return data

        except httpx.HTTPStatusError as e:
            log.warning(f"Página {page}, tentativa {attempt}: HTTP {e.response.status_code}")
        except httpx.TimeoutException:
            log.warning(f"Página {page}, tentativa {attempt}: timeout")
        except Exception as e:
            log.warning(f"Página {page}, tentativa {attempt}: {e}")

        if attempt < MAX_RETRIES:
            wait = RETRY_BACKOFF * attempt
            log.info(f"Aguardando {wait}s antes de tentar novamente...")
            time.sleep(wait)

    stats.errors += 1
    log.error(f"Página {page}: falhou após {MAX_RETRIES} tentativas.")
    return None


# ---------------------------------------------------------------------------
# Lógica de upsert no PostgreSQL
# ---------------------------------------------------------------------------

UPSERT_MARCA = """
    INSERT INTO marcas (nome)
    VALUES (%s)
    ON CONFLICT (nome) DO NOTHING
    RETURNING id
"""

UPSERT_MODELO = """
    INSERT INTO modelos (nome, marca_id)
    VALUES (%s, (SELECT id FROM marcas WHERE nome = %s))
    ON CONFLICT (nome, marca_id) DO NOTHING
    RETURNING id
"""

UPSERT_VEHICLE = """
    INSERT INTO vehicles (chassi, placa, marca_nome, modelo_nome, ano_fabricacao, ano_modelo,
                          combustivel, potencia, cod_modelo, subsegmento, segmento)
    VALUES (%(chassi)s, %(placa)s, %(marca_nome)s, %(modelo_nome)s,
            %(ano_fabricacao)s, %(ano_modelo)s, %(combustivel)s, %(potencia)s,
            %(cod_modelo)s, %(subsegmento)s, %(segmento)s)
    ON CONFLICT (chassi) DO UPDATE SET
        placa = EXCLUDED.placa,
        marca_nome = EXCLUDED.marca_nome,
        modelo_nome = EXCLUDED.modelo_nome,
        combustivel = EXCLUDED.combustivel,
        potencia = EXCLUDED.potencia,
        updated_at = NOW()
    RETURNING id
"""

UPSERT_EMPRESA = """
    INSERT INTO empresas (cnpj, razao_social, tipo_proprietario, cod_cnae, atividade_economica,
                          data_abertura, segmento_cliente)
    VALUES (%(cnpj)s, %(razao_social)s, %(tipo_proprietario)s, %(cod_cnae)s,
            %(atividade_economica)s, %(data_abertura)s, %(segmento_cliente)s)
    ON CONFLICT (cnpj) DO UPDATE SET
        razao_social = EXCLUDED.razao_social,
        cod_cnae = EXCLUDED.cod_cnae,
        atividade_economica = EXCLUDED.atividade_economica,
        updated_at = NOW()
    RETURNING id
"""

UPSERT_ENDERECO = """
    INSERT INTO enderecos (empresa_id, logradouro, numero, complemento, bairro, cidade, uf, cep)
    VALUES (%(empresa_id)s, %(logradouro)s, %(numero)s, %(complemento)s,
            %(bairro)s, %(cidade)s, %(uf)s, %(cep)s)
    ON CONFLICT (empresa_id) DO UPDATE SET
        logradouro = EXCLUDED.logradouro,
        numero = EXCLUDED.numero,
        cidade = EXCLUDED.cidade,
        uf = EXCLUDED.uf,
        cep = EXCLUDED.cep
"""

UPSERT_CONTATO = """
    INSERT INTO contatos (empresa_id, ddd1, telefone1, ddd2, telefone2, ddd3, telefone3,
                          ddd_celular1, celular1, email)
    VALUES (%(empresa_id)s, %(ddd1)s, %(telefone1)s, %(ddd2)s, %(telefone2)s, %(ddd3)s,
            %(telefone3)s, %(ddd_celular1)s, %(celular1)s, %(email)s)
    ON CONFLICT (empresa_id) DO UPDATE SET
        ddd1 = EXCLUDED.ddd1,
        telefone1 = EXCLUDED.telefone1,
        email = EXCLUDED.email
"""

UPSERT_REGISTRATION = """
    INSERT INTO registrations (
        chassi, placa, vehicle_id, empresa_id,
        data_emplacamento, data_atualizacao,
        municipio_emplacamento, cod_municipio, uf_emplacamento,
        preco, preco_validado,
        concessionario, cnpj_concessionario,
        marca_nome, modelo_nome, ano_fabricacao, ano_modelo
    )
    VALUES (
        %(chassi)s, %(placa)s, %(vehicle_id)s, %(empresa_id)s,
        %(data_emplacamento)s, %(data_atualizacao)s,
        %(municipio)s, %(cod_municipio)s, %(uf)s,
        %(preco)s, %(preco_validado)s,
        %(concessionario)s, %(cnpj_concessionario)s,
        %(marca_nome)s, %(modelo_nome)s, %(ano_fabricacao)s, %(ano_modelo)s
    )
    ON CONFLICT (chassi, data_emplacamento) DO UPDATE SET
        preco = EXCLUDED.preco,
        preco_validado = EXCLUDED.preco_validado,
        data_atualizacao = EXCLUDED.data_atualizacao,
        concessionario = EXCLUDED.concessionario,
        updated_at = NOW()
    RETURNING id
"""


def _safe_int(val) -> Optional[int]:
    try:
        return int(val) if val else None
    except (ValueError, TypeError):
        return None


def _safe_float(val) -> Optional[float]:
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _safe_date(val: str) -> Optional[str]:
    """Valida formato de data yyyy-MM-dd."""
    if not val:
        return None
    try:
        datetime.strptime(val, "%Y-%m-%d")
        return val
    except ValueError:
        return None


def upsert_record(cur, record: dict, stats: SyncStats, dry_run: bool = False) -> bool:
    """
    Processa um registro da API e faz upsert nas tabelas vehicles, empresas e registrations.
    Retorna True se bem-sucedido.
    """
    try:
        # --- Vehicle ---
        vehicle_params = {
            "chassi": record.get("chassi", "").strip(),
            "placa": record.get("placa", "").strip(),
            "marca_nome": record.get("marca", "").strip(),
            "modelo_nome": record.get("modelo", "").strip(),
            "ano_fabricacao": _safe_int(record.get("anofabricacao")),
            "ano_modelo": _safe_int(record.get("anomodelo")),
            "combustivel": record.get("combustivel", "").strip() or None,
            "potencia": record.get("potencia", "").strip() or None,
            "cod_modelo": record.get("cod_modelo", "").strip() or None,
            "subsegmento": record.get("subsegmento", "").strip() or None,
            "segmento": record.get("segmento", "").strip() or None,
        }

        if not vehicle_params["chassi"]:
            log.debug("Registro sem chassi — ignorado.")
            return False

        if dry_run:
            stats.vehicles_upserted += 1
        else:
            cur.execute(UPSERT_VEHICLE, vehicle_params)
            row = cur.fetchone()
            vehicle_id = row[0] if row else None
            if vehicle_id is None:
                cur.execute("SELECT id FROM vehicles WHERE chassi = %s", (vehicle_params["chassi"],))
                row = cur.fetchone()
                vehicle_id = row[0] if row else None
            stats.vehicles_upserted += 1

        # --- Empresa ---
        cnpj = record.get("C_CPFCNPJPROPRIETARIO", "").strip()
        if not cnpj:
            return True  # Veículo sem proprietário identificado — ainda válido

        empresa_params = {
            "cnpj": cnpj,
            "razao_social": record.get("C_NOMEPROPRIETARIO", "").strip() or None,
            "tipo_proprietario": record.get("C_TIPOCNPJPROPRIETARIO", "").strip() or None,
            "cod_cnae": record.get("cod_atividadeEconomica", "").strip() or None,
            "atividade_economica": record.get("atividadeEconomica", "").strip() or None,
            "data_abertura": record.get("dataAbertura", "").strip() or None,
            "segmento_cliente": None,  # não vem da API, enriquecido internamente
        }

        if dry_run:
            empresa_id = 0
            stats.empresas_upserted += 1
        else:
            cur.execute(UPSERT_EMPRESA, empresa_params)
            row = cur.fetchone()
            empresa_id = row[0] if row else None
            if empresa_id is None:
                cur.execute("SELECT id FROM empresas WHERE cnpj = %s", (cnpj,))
                row = cur.fetchone()
                empresa_id = row[0] if row else None
            stats.empresas_upserted += 1

            if empresa_id:
                # Endereço
                cur.execute(UPSERT_ENDERECO, {
                    "empresa_id": empresa_id,
                    "logradouro": record.get("C_NO_LOGR", "").strip() or None,
                    "numero": record.get("C_NU_LOGR", "").strip() or None,
                    "complemento": record.get("C_NO_COMPL", "").strip() or None,
                    "bairro": record.get("C_NO_BAIRRO", "").strip() or None,
                    "cidade": record.get("C_NO_CIDADE", "").strip() or None,
                    "uf": record.get("C_SG_ESTADO", "").strip() or None,
                    "cep": record.get("C_NU_CEP", "").strip() or None,
                })

                # Contatos
                cur.execute(UPSERT_CONTATO, {
                    "empresa_id": empresa_id,
                    "ddd1": record.get("C_DDD1", "").strip() or None,
                    "telefone1": record.get("C_TELEFONE1", "").strip() or None,
                    "ddd2": record.get("C_DDD2", "").strip() or None,
                    "telefone2": record.get("C_TELEFONE2", "").strip() or None,
                    "ddd3": record.get("C_DDD3", "").strip() or None,
                    "telefone3": record.get("C_TELEFONE3", "").strip() or None,
                    "ddd_celular1": record.get("C_DDD_CELULAR1", "").strip() or None,
                    "celular1": record.get("C_CELULAR1", "").strip() or None,
                    "email": record.get("C_EMAIL", "").strip() or None,
                })

        # --- Registration ---
        preco_validado_raw = record.get("preco_validado", "")
        preco_validado = True if str(preco_validado_raw).upper() == "SIM" else (
            False if str(preco_validado_raw).upper() == "NÃO" else None
        )

        reg_params = {
            "chassi": vehicle_params["chassi"],
            "placa": vehicle_params["placa"],
            "vehicle_id": vehicle_id if not dry_run else None,
            "empresa_id": empresa_id if not dry_run else None,
            "data_emplacamento": _safe_date(record.get("data_emplacamento")),
            "data_atualizacao": _safe_date(record.get("data_atualizacao")),
            "municipio": record.get("municipio", "").strip() or None,
            "cod_municipio": record.get("cod_municipio", "").strip() or None,
            "uf": record.get("estado", "").strip() or None,
            "preco": _safe_float(record.get("preco")),
            "preco_validado": preco_validado,
            "concessionario": record.get("concessionario", "").strip() or None,
            "cnpj_concessionario": record.get("cnpj_concessionario", "").strip() or None,
            "marca_nome": vehicle_params["marca_nome"],
            "modelo_nome": vehicle_params["modelo_nome"],
            "ano_fabricacao": vehicle_params["ano_fabricacao"],
            "ano_modelo": vehicle_params["ano_modelo"],
        }

        if not dry_run:
            cur.execute(UPSERT_REGISTRATION, reg_params)

        stats.registrations_upserted += 1
        return True

    except Exception as e:
        log.warning(f"Erro ao processar registro (chassi={record.get('chassi')}): {e}")
        stats.errors += 1
        return False


# ---------------------------------------------------------------------------
# Log de sync na tabela sync_logs
# ---------------------------------------------------------------------------

def log_sync_start(conn, mode: str, date_range: str, date_type: str) -> Optional[int]:
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sync_logs (mode, date_range, date_type, status, started_at)
            VALUES (%s, %s, %s, 'running', NOW())
            RETURNING id
        """, (mode, date_range, date_type))
        conn.commit()
        row = cur.fetchone()
        return row[0] if row else None
    except Exception as e:
        log.warning(f"Não foi possível registrar início do sync: {e}")
        return None


def log_sync_end(conn, sync_id: Optional[int], stats: SyncStats, success: bool):
    if sync_id is None:
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE sync_logs SET
                status = %s,
                records_fetched = %s,
                records_upserted = %s,
                errors = %s,
                finished_at = NOW(),
                duration_seconds = %s
            WHERE id = %s
        """, (
            "success" if success else "failed",
            stats.records_fetched,
            stats.registrations_upserted,
            stats.errors,
            int(stats.elapsed_seconds()),
            sync_id,
        ))
        conn.commit()
    except Exception as e:
        log.warning(f"Não foi possível atualizar sync_log {sync_id}: {e}")


# ---------------------------------------------------------------------------
# Orquestração principal
# ---------------------------------------------------------------------------

def run_sync(
    mode: str = "incremental",
    days: int = 7,
    date_range_str: Optional[str] = None,
    date_type: str = "atualizacao",
    dry_run: bool = False,
):
    """
    Executa o sync completo da API para o PostgreSQL.

    Args:
        mode: 'incremental' (últimos N dias) ou 'full' (range explícito)
        days: número de dias para modo incremental (padrão: 7)
        date_range_str: range explícito no formato yyyy-MM-dd:yyyy-MM-dd
        date_type: 'atualizacao' (padrão, para sync diário) ou 'emplacamento' (histórico)
        dry_run: se True, busca da API mas NÃO grava no banco
    """
    if not API_KEY:
        log.error("HUBQUEST_API_KEY não configurada. Abortando.")
        sys.exit(1)

    if not DATABASE_URL and not dry_run:
        log.error("DATABASE_URL não configurada. Abortando.")
        sys.exit(1)

    # Determinar date_range
    if mode == "incremental":
        # Recomendação da API: usar date_type=atualizacao com mínimo 5 dias
        effective_days = max(days, 5)
        date_range = str(effective_days)
        log.info(f"Modo: incremental | date_range={date_range} dias | date_type={date_type}")
    else:
        if not date_range_str:
            # Padrão: últimos 90 dias (máximo da API)
            end = datetime.now()
            start = end - timedelta(days=89)
            date_range_str = f"{start.strftime('%Y-%m-%d')}:{end.strftime('%Y-%m-%d')}"
        date_range = date_range_str
        log.info(f"Modo: full | date_range={date_range} | date_type={date_type}")

    if dry_run:
        log.info("🔍 DRY RUN ativado — nenhum dado será gravado no banco.")

    stats = SyncStats()

    # Conectar ao banco (se não dry_run)
    conn = None
    sync_id = None
    if not dry_run:
        try:
            conn = get_db_connection()
            conn.autocommit = False
            log.info("Conexão com PostgreSQL estabelecida.")
            sync_id = log_sync_start(conn, mode, date_range, date_type)
        except Exception as e:
            log.error(f"Falha ao conectar ao banco: {e}")
            sys.exit(1)

    # Cliente HTTP com autenticação
    headers = {"key": API_KEY, "Content-Type": "application/json"}

    with httpx.Client(headers=headers, follow_redirects=True) as client:
        # Warm-up da API
        warmup_api(client)

        # Buscar primeira página para saber o total
        log.info("Buscando página 0 para determinar total de registros...")
        first_page = fetch_page(client, date_range, date_type, page=0, stats=stats)

        if not first_page:
            log.warning("API não retornou dados. Sync encerrado sem registros.")
            if conn:
                log_sync_end(conn, sync_id, stats, success=True)
                conn.close()
            return

        total_records = first_page.get("pagination", {}).get("total", 0)
        per_page = first_page.get("pagination", {}).get("perPage", PAGE_SIZE)
        total_pages = -(-total_records // per_page)  # ceil division

        log.info(f"Total de registros: {total_records:,} | Páginas: {total_pages} | Por página: {per_page}")

        # Processar todas as páginas
        cur = conn.cursor() if conn else None
        inserted_since_commit = 0

        for page_num in range(0, total_pages):
            if page_num == 0:
                page_data = first_page
            else:
                page_data = fetch_page(client, date_range, date_type, page=page_num, stats=stats)

            if not page_data:
                log.warning(f"Página {page_num} vazia ou erro. Pulando...")
                continue

            records = page_data.get("results", [])
            stats.pages_fetched += 1
            stats.records_fetched += len(records)

            for record in records:
                ok = upsert_record(cur, record, stats, dry_run=dry_run)
                if ok and not dry_run:
                    inserted_since_commit += 1

                # Commit periódico para evitar transações gigantes
                if not dry_run and inserted_since_commit >= COMMIT_EVERY_N:
                    try:
                        conn.commit()
                        inserted_since_commit = 0
                        log.debug(f"Commit intermediário após {COMMIT_EVERY_N} registros.")
                    except Exception as e:
                        log.error(f"Falha no commit intermediário: {e}")
                        conn.rollback()

            # Log de progresso a cada página
            pct = (page_num + 1) / total_pages * 100
            log.info(
                f"Página {page_num + 1}/{total_pages} ({pct:.1f}%) | "
                f"Fetched: {stats.records_fetched:,} | "
                f"Erros: {stats.errors} | "
                f"Taxa: {stats.rate():.1f}/s"
            )

        # Commit final
        if not dry_run and conn:
            try:
                conn.commit()
                log.info("Commit final realizado.")
            except Exception as e:
                log.error(f"Falha no commit final: {e}")
                conn.rollback()

    # Finalizar
    success = stats.errors < stats.records_fetched * 0.05  # menos de 5% de erros = sucesso
    log.info("=" * 60)
    log.info("SYNC CONCLUÍDO")
    log.info("=" * 60)
    log.info(stats.summary())
    log.info(f"Status: {'✅ SUCESSO' if success else '⚠️  SUCESSO COM ERROS'}")
    log.info(f"Log salvo em: {LOG_FILE}")

    if conn:
        log_sync_end(conn, sync_id, stats, success=success)
        conn.close()


# ---------------------------------------------------------------------------
# Criação da tabela sync_logs se não existir
# ---------------------------------------------------------------------------

SYNC_LOGS_DDL = """
CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    mode VARCHAR(20) NOT NULL,
    date_range VARCHAR(50),
    date_type VARCHAR(20),
    status VARCHAR(20) DEFAULT 'running',
    records_fetched INTEGER DEFAULT 0,
    records_upserted INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    notes TEXT
);
"""

VEHICLES_EXTRA_COLUMNS = """
DO $$
BEGIN
    -- Adicionar colunas extras ao vehicles se não existirem
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='vehicles' AND column_name='combustivel') THEN
        ALTER TABLE vehicles ADD COLUMN combustivel VARCHAR(50);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='vehicles' AND column_name='potencia') THEN
        ALTER TABLE vehicles ADD COLUMN potencia VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='vehicles' AND column_name='cod_modelo') THEN
        ALTER TABLE vehicles ADD COLUMN cod_modelo VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='vehicles' AND column_name='subsegmento') THEN
        ALTER TABLE vehicles ADD COLUMN subsegmento VARCHAR(50);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='vehicles' AND column_name='segmento') THEN
        ALTER TABLE vehicles ADD COLUMN segmento VARCHAR(50);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='vehicles' AND column_name='updated_at') THEN
        ALTER TABLE vehicles ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END;
$$;
"""

REGISTRATIONS_EXTRA_COLUMNS = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='registrations' AND column_name='data_atualizacao') THEN
        ALTER TABLE registrations ADD COLUMN data_atualizacao DATE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='registrations' AND column_name='concessionario') THEN
        ALTER TABLE registrations ADD COLUMN concessionario VARCHAR(200);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='registrations' AND column_name='cnpj_concessionario') THEN
        ALTER TABLE registrations ADD COLUMN cnpj_concessionario VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='registrations' AND column_name='updated_at') THEN
        ALTER TABLE registrations ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
    -- Constraint de unicidade para upsert idempotente
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints
                   WHERE table_name='registrations' AND constraint_name='uq_registrations_chassi_data') THEN
        ALTER TABLE registrations
            ADD CONSTRAINT uq_registrations_chassi_data UNIQUE (chassi, data_emplacamento);
    END IF;
END;
$$;
"""

EMPRESAS_EXTRA_COLUMNS = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='empresas' AND column_name='tipo_proprietario') THEN
        ALTER TABLE empresas ADD COLUMN tipo_proprietario VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='empresas' AND column_name='cod_cnae') THEN
        ALTER TABLE empresas ADD COLUMN cod_cnae VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='empresas' AND column_name='atividade_economica') THEN
        ALTER TABLE empresas ADD COLUMN atividade_economica TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='empresas' AND column_name='data_abertura') THEN
        ALTER TABLE empresas ADD COLUMN data_abertura VARCHAR(20);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='empresas' AND column_name='updated_at') THEN
        ALTER TABLE empresas ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END;
$$;
"""


def setup_db_schema():
    """Garante que todas as tabelas e colunas necessárias existem."""
    log.info("Verificando/criando schema necessário...")
    try:
        conn = get_db_connection()
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(SYNC_LOGS_DDL)
        cur.execute(VEHICLES_EXTRA_COLUMNS)
        cur.execute(REGISTRATIONS_EXTRA_COLUMNS)
        cur.execute(EMPRESAS_EXTRA_COLUMNS)
        cur.close()
        conn.close()
        log.info("Schema verificado/atualizado com sucesso.")
    except Exception as e:
        log.warning(f"Não foi possível atualizar schema (pode já estar correto): {e}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="FleetIntel MCP — Sync de emplacamentos via API externa",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Sync diário incremental (últimos 7 dias, recomendado)
  python scripts/sync_from_api.py

  # Sync dos últimos 3 dias
  python scripts/sync_from_api.py --days 3

  # Backfill de um mês específico
  python scripts/sync_from_api.py --mode full --date-range 2024-12-01:2024-12-31 --date-type emplacamento

  # Simular sem gravar
  python scripts/sync_from_api.py --dry-run
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["incremental", "full"],
        default="incremental",
        help="Modo de sync: incremental (últimos N dias) ou full (range explícito)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Número de dias para modo incremental (padrão: 7, mínimo: 5)",
    )
    parser.add_argument(
        "--date-range",
        dest="date_range",
        default=None,
        help="Range de datas para modo full: yyyy-MM-dd:yyyy-MM-dd",
    )
    parser.add_argument(
        "--date-type",
        dest="date_type",
        choices=["atualizacao", "emplacamento"],
        default="atualizacao",
        help="Tipo de data: atualizacao (sync diário) ou emplacamento (histórico)",
    )
    parser.add_argument(
        "--skip-schema-setup",
        action="store_true",
        help="Pular criação/verificação de schema (use quando já configurado)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula o sync sem gravar no banco (útil para testar autenticação e volume)",
    )

    args = parser.parse_args()

    log.info("=" * 60)
    log.info("FleetIntel MCP — Sync de Dados")
    log.info("=" * 60)
    log.info(f"Modo: {args.mode} | date_type: {args.date_type} | dry_run: {args.dry_run}")

    # Setup schema se necessário
    if not args.skip_schema_setup and not args.dry_run:
        setup_db_schema()

    run_sync(
        mode=args.mode,
        days=args.days,
        date_range_str=args.date_range,
        date_type=args.date_type,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
