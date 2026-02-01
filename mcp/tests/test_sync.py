import pytest
from unittest.mock import AsyncMock, patch
from jobs.incremental_sync import (
    get_last_successful_sync,
    warm_up_api,
    run_incremental_sync,
    handle_sync_error
)
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_get_last_successful_sync_no_history():
    """Testa quando não há histórico de sincronização"""
    mock_pool = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value.fetchrow.return_value = None
    
    result = await get_last_successful_sync(mock_pool)
    expected = datetime.now() - timedelta(days=8)
    
    # Comparação aproximada (diferença máxima de 1 segundo)
    assert abs((result - expected).total_seconds()) < 1

@pytest.mark.asyncio
async def test_warm_up_api_success():
    """Testa warm-up bem-sucedido"""
    mock_client = AsyncMock()
    mock_client.get.return_value.raise_for_status.return_value = None
    
    await warm_up_api(mock_client)
    mock_client.get.assert_called_once()

@pytest.mark.asyncio
async def test_warm_up_api_timeout():
    """Testa timeout no warm-up"""
    mock_client = AsyncMock()
    mock_client.get.side_effect = TimeoutError("Timeout")
    
    with patch("builtins.print") as mock_print:
        await warm_up_api(mock_client)
        mock_print.assert_called_with("⚠️ Falha no warm-up: Timeout")

@pytest.mark.asyncio
async def test_run_incremental_sync_success():
    """Testa fluxo completo de sincronização"""
    mock_pool = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value.fetchval.return_value = 1
    
    with patch("jobs.incremental_sync.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value.json.return_value = {
            "results": [{"id": i} for i in range(100)],
            "next_page": None
        }
        
        await run_incremental_sync(mock_pool)
        
        # Verifica se atualizou o status para sucesso
        mock_pool.acquire.return_value.__aenter__.return_value.execute.assert_called_with(
            "UPDATE sync_logs SET status = $1, records_fetched = $2, records_processed = $3, completed_at = $4 WHERE id = $5",
            'success', 100, 0, pytest.any(datetime), 1
        )

@pytest.mark.asyncio
async def test_handle_sync_error_retry():
    """Testa lógica de retentativa após erro"""
    mock_pool = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value.fetchval.return_value = 0
    
    error = Exception("Test error")
    sync_id = 1
    
    with patch("asyncio.sleep", new_callable=AsyncMock), \
         patch("jobs.incremental_sync.run_incremental_sync", new_callable=AsyncMock) as mock_retry:
        
        await handle_sync_error(mock_pool, sync_id, error)
        
        # Verifica se agendou retentativa
        mock_retry.assert_called_once_with(mock_pool)
        mock_pool.acquire.return_value.__aenter__.return_value.execute.assert_called_with(
            "UPDATE sync_logs SET status = $1, error_message = $2, retry_count = $3, completed_at = $4 WHERE id = $5",
            'failed', 'Test error', 1, pytest.any(datetime), 1
        )
