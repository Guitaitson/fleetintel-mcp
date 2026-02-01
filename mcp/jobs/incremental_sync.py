import asyncio
import httpx
import asyncpg
from datetime import datetime, timedelta
from typing import Optional

# Configurações da API (ATUALIZAR COM DADOS REAIS)
HUBQUEST_API_URL = "https://api.hubquest.com/v1/data"
API_KEY = "your_api_key_here"
TIMEOUT = 10.0
WARMUP_TIMEOUT = 60.0

async def get_last_successful_sync(pool: asyncpg.Pool) -> datetime:
    """Obtém a última sincronização bem-sucedida do banco de dados"""
    async with pool.acquire() as conn:
        record = await conn.fetchrow(
            "SELECT date_range_end FROM sync_logs "
            "WHERE status = 'success' "
            "ORDER BY completed_at DESC LIMIT 1"
        )
        if record:
            return record['date_range_end']
        return datetime.now() - timedelta(days=8)

async def warm_up_api(client: httpx.AsyncClient):
    """Executa uma requisição simples para aquecer a API"""
    try:
        start_time = datetime.now()
        response = await client.get(
            f"{HUBQUEST_API_URL}?top=1",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=WARMUP_TIMEOUT
        )
        response.raise_for_status()
        duration = (datetime.now() - start_time).total_seconds()
        print(f"✅ Warm-up realizado em {duration:.2f}s")
    except Exception as e:
        print(f"⚠️ Falha no warm-up: {str(e)}")

async def run_incremental_sync(pool: asyncpg.Pool):
    """Executa o processo de sincronização incremental"""
    # 1. Registrar início da sincronização
    sync_id = await create_sync_log(pool, "running")
    
    try:
        # 2. Obter último sync bem-sucedido
        last_sync = await get_last_successful_sync(pool)
        date_range_start = last_sync - timedelta(days=1)  # Overlap de 1 dia
        date_range_end = datetime.now()
        
        # 3. Configurar cliente HTTP
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # 4. Aquecer API se for primeira sincronização do dia
            if datetime.now().hour < 1:  # Execução após meia-noite
                await warm_up_api(client)
            
            # 5. Executar sincronização paginada
            page = 1
            records_fetched = 0
            records_processed = 0
            
            while True:
                # 6. Buscar dados da API
                response = await client.get(
                    f"{HUBQUEST_API_URL}?date_type=atualizacao"
                    f"&start_date={date_range_start.strftime('%Y-%m-%d')}"
                    f"&end_date={date_range_end.strftime('%Y-%m-%d')}"
                    f"&page={page}",
                    headers={"Authorization": f"Bearer {API_KEY}"}
                )
                response.raise_for_status()
                data = response.json()
                
                # 7. Processar registros (implementar upsert)
                # records_processed += await process_records(pool, data['results'])
                records_fetched += len(data['results'])
                
                # 8.1 Coletar métricas de desempenho
                duration = (datetime.now() - start_time).total_seconds()
                metrics = {
                    "sync_id": sync_id,
                    "page": page,
                    "duration_seconds": duration,
                    "records_per_second": len(data['results']) / duration if duration > 0 else 0,
                    "timestamp": datetime.now().isoformat()
                }
                print(f"📊 Métricas: {metrics}")
                
                # 8. Atualizar log de sincronização
                await update_sync_log(
                    pool, sync_id,
                    records_fetched=records_fetched,
                    records_processed=records_processed
                )
                
                # 9. Verificar próxima página
                if not data.get('next_page'):
                    break
                page += 1
        
        # 10. Marcar como sucesso
        await update_sync_log(
            pool, sync_id,
            status='success',
            completed_at=datetime.now()
        )
        print("✅ Sincronização incremental concluída com sucesso!")
        
    except Exception as e:
        # 11. Tratamento de erros
        await handle_sync_error(pool, sync_id, e)

async def create_sync_log(pool: asyncpg.Pool, status: str) -> int:
    """Cria registro inicial no log de sincronização"""
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "INSERT INTO sync_logs (started_at, status) "
            "VALUES ($1, $2) RETURNING id",
            datetime.now(), status
        )

async def update_sync_log(
    pool: asyncpg.Pool,
    sync_id: int,
    status: Optional[str] = None,
    records_fetched: int = 0,
    records_processed: int = 0,
    completed_at: Optional[datetime] = None
):
    """Atualiza registro de sincronização"""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE sync_logs SET "
            "status = COALESCE($1, status), "
            "records_fetched = $2, "
            "records_processed = $3, "
            "completed_at = COALESCE($4, completed_at) "
            "WHERE id = $5",
            status, records_fetched, records_processed, completed_at, sync_id
        )

async def handle_sync_error(pool: asyncpg.Pool, sync_id: int, error: Exception):
    """Trata erros durante a sincronização"""
    error_msg = str(error)[:500]  # Limitar tamanho da mensagem
    print(f"❌ Erro na sincronização: {error_msg}")
    
    async with pool.acquire() as conn:
        # Atualizar contagem de retentativas
        retry_count = await conn.fetchval(
            "SELECT retry_count FROM sync_logs WHERE id = $1", sync_id
        ) or 0
        
        await conn.execute(
            "UPDATE sync_logs SET "
            "status = 'failed', "
            "error_message = $1, "
            "retry_count = $2, "
            "completed_at = $3 "
            "WHERE id = $4",
            error_msg, retry_count + 1, datetime.now(), sync_id
        )
        
        # Agendar retentativa se necessário
        if retry_count < 3:
            retry_delay = 2 ** retry_count  # Backoff exponencial em minutos
            print(f"⏱ Agendando retentativa em {retry_delay} minutos...")
            await asyncio.sleep(retry_delay * 60)
            await run_incremental_sync(pool)

# Função principal para execução agendada
async def main():
    # Configurar pool de conexão com o Supabase
    pool = await asyncpg.create_pool(
        user='your_db_user',
        password='your_db_password',
        database='your_db_name',
        host='your_db_host'
    )
    
    try:
        await run_incremental_sync(pool)
    finally:
        await pool.close()

if __name__ == "__main__":
    asyncio.run(main())
