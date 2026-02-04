"""
Incremental Sync Job - Sincronizacao semanal de veiculos

Executa sincronizacao incremental com:
- APScheduler para agendamento
- Retry com backoff
- Logging estruturado
- Metrics e monitoramento
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clients.hubquest_client import (
    HubQuestClient,
    APIConfig,
    SyncResult,
    APIError,
    create_client
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text, func
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SyncConfig:
    """Configuracao do job de sincronizacao"""
    # API
    api_url: str = "https://api.hubquest.com/v1"
    api_key: str = ""
    
    # Database
    database_url: str = ""
    
    # Scheduling
    schedule_day: str = "sunday"  # sunday, monday, tuesday, etc.
    schedule_time: str = "22:00"   # HH:MM
    
    # Sync options
    date_type: str = "atualizacao"
    state_filter: Optional[str] = None  # None = todas as UFs
    batch_size: int = 1000
    overlap_days: int = 1  # Dias de overlap com ultima sync
    
    # Retry
    max_retries: int = 3
    retry_delay: float = 60.0  # segundos
    
    # Logging
    log_to_database: bool = True
    log_level: str = "INFO"


class SyncLogger:
    """Logger de sincronizacao para banco de dados"""
    
    def __init__(self, engine):
        self.engine = engine
    
    async def log_start(self, sync_type: str) -> int:
        """Registra inicio de sincronizacao"""
        async with self.engine.begin() as conn:
            result = await conn.execute(
                text("""
                    INSERT INTO sync_logs (sync_type, status, started_at)
                    VALUES (:sync_type, 'running', :started_at)
                    RETURNING id
                """),
                {
                    "sync_type": sync_type,
                    "started_at": datetime.now()
                }
            )
            return result.scalar()
    
    async def log_progress(
        self,
        sync_id: int,
        records_fetched: int = 0,
        records_processed: int = 0,
        pages_processed: int = 0,
        current_page: int = None,
        status: str = "running"
    ):
        """Registra progresso"""
        async with self.engine.begin() as conn:
            await conn.execute(
                text("""
                    UPDATE sync_logs SET
                        records_fetched = :records_fetched,
                        records_processed = :records_processed,
                        pages_processed = :pages_processed,
                        current_page = :current_page,
                        status = :status,
                        updated_at = :updated_at
                    WHERE id = :sync_id
                """),
                {
                    "sync_id": sync_id,
                    "records_fetched": records_fetched,
                    "records_processed": records_processed,
                    "pages_processed": pages_processed,
                    "current_page": current_page,
                    "status": status,
                    "updated_at": datetime.now()
                }
            )
    
    async def log_success(
        self,
        sync_id: int,
        records_fetched: int,
        records_inserted: int,
        records_updated: int,
        records_skipped: int,
        duration_seconds: float
    ):
        """Registra sucesso"""
        async with self.engine.begin() as conn:
            await conn.execute(
                text("""
                    UPDATE sync_logs SET
                        status = 'success',
                        records_fetched = :records_fetched,
                        records_inserted = :records_inserted,
                        records_updated = :records_updated,
                        records_skipped = :records_skipped,
                        duration_seconds = :duration_seconds,
                        completed_at = :completed_at
                    WHERE id = :sync_id
                """),
                {
                    "sync_id": sync_id,
                    "records_fetched": records_fetched,
                    "records_inserted": records_inserted,
                    "records_updated": records_updated,
                    "records_skipped": records_skipped,
                    "duration_seconds": duration_seconds,
                    "completed_at": datetime.now()
                }
            )
    
    async def log_error(
        self,
        sync_id: int,
        error_message: str,
        error_type: str = "general"
    ):
        """Registra erro"""
        async with self.engine.begin() as conn:
            await conn.execute(
                text("""
                    UPDATE sync_logs SET
                        status = 'failed',
                        error_type = :error_type,
                        error_message = :error_message,
                        completed_at = :completed_at
                    WHERE id = :sync_id
                """),
                {
                    "sync_id": sync_id,
                    "error_type": error_type,
                    "error_message": error_message[:1000],
                    "completed_at": datetime.now()
                }
            )
    
    async def get_last_successful_sync(self) -> Optional[datetime]:
        """Obtem data do ultimo sync bem-sucedido"""
        async with self.engine.begin() as conn:
            result = await conn.execute(
                text("""
                    SELECT completed_at FROM sync_logs
                    WHERE sync_type = 'incremental'
                    AND status = 'success'
                    ORDER BY completed_at DESC
                    LIMIT 1
                """)
            )
            row = result.fetchone()
            return row[0] if row else None


class IncrementalSyncJob:
    """Job de sincronizacao incremental"""
    
    def __init__(self, config: SyncConfig):
        self.config = config
        self.engine = None
        self.scheduler = None
        self.sync_logger = None
        self._running = False
    
    async def initialize(self):
        """Inicializa o job"""
        # Create database engine
        self.engine = create_async_engine(
            self.config.database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
        
        # Initialize logger
        self.sync_logger = SyncLogger(self.engine)
        
        logger.info("IncrementalSyncJob inicializado")
    
    async def shutdown(self):
        """Finaliza o job"""
        if self.scheduler:
            self.scheduler.shutdown()
        
        if self.engine:
            await self.engine.dispose()
        
        logger.info("IncrementalSyncJob finalizado")
    
    def _transform_vehicle(self, api_record: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma registro da API para formato do banco"""
        return {
            "chassi": api_record.get("chassi", ""),
            "placa": api_record.get("placa", ""),
            "marca": api_record.get("marca", ""),
            "modelo": api_record.get("modelo", ""),
            "ano_fabricacao": api_record.get("ano_fabricacao"),
            "ano_modelo": api_record.get("ano_modelo"),
            "cpf_cnpj_proprietario": api_record.get("cpf_cnpj", ""),
            "nome_proprietario": api_record.get("nome_proprietario", ""),
            "uf_proprietario": api_record.get("uf_proprietario", ""),
            "cidade_proprietario": api_record.get("cidade_proprietario", ""),
            "data_emplacamento": api_record.get("data_emplacamento"),
            "municipio_emplacamento": api_record.get("municipio_emplacamento", ""),
            "uf_emplacamento": api_record.get("uf_emplacamento", ""),
            "preco": api_record.get("preco"),
            "preco_validado": api_record.get("preco_validado", False),
            "source": "hubquest",
            "updated_at": datetime.now()
        }
    
    async def _upsert_vehicle(self, conn, record: Dict[str, Any]):
        """Faz upsert de um veiculo"""
        await conn.execute(
            text("""
                INSERT INTO vehicles (
                    chassi, placa, marca, modelo, ano_fabricacao, ano_modelo,
                    marca_nome, modelo_nome, source, updated_at
                ) VALUES (
                    :chassi, :placa, :marca, :modelo, :ano_fabricacao, :ano_modelo,
                    :marca, :modelo, :source, :updated_at
                )
                ON CONFLICT (chassi) DO UPDATE SET
                    placa = EXCLUDED.placa,
                    modelo = EXCLUDED.modelo,
                    ano_fabricacao = EXCLUDED.ano_fabricacao,
                    ano_modelo = EXCLUDED.ano_modelo,
                    source = EXCLUDED.source,
                    updated_at = EXCLUDED.updated_at
                RETURNING id
            """),
            record
        )
    
    async def run(self) -> SyncResult:
        """Executa a sincronizacao incremental"""
        if self._running:
            logger.warning("Sync ja em execucao, ignorando...")
            return SyncResult(success=False)
        
        self._running = True
        start_time = datetime.now()
        result = SyncResult(success=False, started_at=start_time)
        
        sync_id = None
        client = None
        
        try:
            # Get last sync date
            last_sync = await self.sync_logger.get_last_successful_sync()
            if last_sync:
                start_date = last_sync - timedelta(days=self.config.overlap_days)
                logger.info(f"Ultimo sync: {last_sync}. Iniciando de {start_date}")
            else:
                start_date = datetime.now() - timedelta(days=8)
                logger.info(f"Primeiro sync. Iniciando de {start_date}")
            
            end_date = datetime.now()
            
            # Log start
            if self.config.log_to_database:
                sync_id = await self.sync_logger.log_start("incremental")
            
            # Create client
            client = await create_client(
                api_key=self.config.api_key,
                base_url=self.config.api_url
            )
            
            # Process pages
            page = 0
            records_fetched = 0
            records_inserted = 0
            records_updated = 0
            
            async for page_data in client.fetch_vehicles_paginated(
                date_type=self.config.date_type,
                start_date=start_date,
                end_date=end_date,
                state=self.config.state_filter
            ):
                page += 1
                results = page_data["results"]
                records_fetched += len(results)
                
                # Process batch
                async with self.engine.begin() as conn:
                    for record in results:
                        try:
                            transformed = self._transform_vehicle(record)
                            vehicle_id = await self._upsert_vehicle(conn, transformed)
                            if vehicle_id:  # Inserted (would be None for update)
                                records_inserted += 1
                            else:
                                records_updated += 1
                        except Exception as e:
                            logger.error(f"Error processing record: {e}")
                            result.errors.append(str(e))
                
                # Log progress
                if self.config.log_to_database and sync_id:
                    await self.sync_logger.log_progress(
                        sync_id=sync_id,
                        records_fetched=records_fetched,
                        records_processed=records_inserted + records_updated,
                        pages_processed=page,
                        current_page=page
                    )
                
                logger.info(f"Page {page}: {len(results)} records")
            
            # Success
            result.success = True
            result.records_fetched = records_fetched
            result.records_inserted = records_inserted
            result.records_updated = records_updated
            result.pages_processed = page
            
            # Log success
            if self.config.log_to_database and sync_id:
                await self.sync_logger.log_success(
                    sync_id=sync_id,
                    records_fetched=records_fetched,
                    records_inserted=records_inserted,
                    records_updated=records_updated,
                    records_skipped=len(result.errors),
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            logger.info(f"Sync completed: {records_fetched} fetched, {records_inserted} inserted, {records_updated} updated")
            
        except APIError as e:
            logger.error(f"API Error: {e}")
            result.errors.append(f"API Error: {e.message}")
            
            if self.config.log_to_database and sync_id:
                await self.sync_logger.log_error(
                    sync_id=sync_id,
                    error_message=e.message,
                    error_type="api_error"
                )
            
        except Exception as e:
            logger.error(f"Sync Error: {e}")
            result.errors.append(str(e))
            
            if self.config.log_to_database and sync_id:
                await self.sync_logger.log_error(
                    sync_id=sync_id,
                    error_message=str(e)[:1000],
                    error_type="sync_error"
                )
        
        finally:
            if client:
                await client.disconnect()
            
            result.completed_at = datetime.now()
            result.duration_seconds = (result.completed_at - start_time).total_seconds()
            self._running = False
        
        return result
    
    def setup_scheduler(self):
        """Configura o agendador"""
        self.scheduler = AsyncIOScheduler()
        
        # Map days
        day_map = {
            "monday": "mon",
            "tuesday": "tue",
            "wednesday": "wed",
            "thursday": "thu",
            "friday": "fri",
            "saturday": "sat",
            "sunday": "sun"
        }
        
        day = day_map.get(self.config.schedule_day.lower(), "sun")
        hour, minute = self.config.schedule_time.split(":")
        
        trigger = CronTrigger(
            day_of_week=day,
            hour=int(hour),
            minute=int(minute)
        )
        
        self.scheduler.add_job(
            self.run,
            trigger=trigger,
            id="incremental_sync",
            name="Incremental Vehicle Sync",
            replace_existing=True,
            max_instances=1
        )
        
        # Add event listeners
        self.scheduler.add_listener(
            self._job_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED
        )
        
        logger.info(f"Scheduler configured: {self.config.schedule_day} at {self.config.schedule_time}")
    
    def _job_listener(self, event):
        """Listener de eventos do scheduler"""
        if event.exception:
            logger.error(f"Job {event.job_id} failed: {event.exception}")
        else:
            logger.info(f"Job {event.job_id} executed successfully")
    
    async def start(self):
        """Inicia o scheduler"""
        if not self.scheduler:
            self.setup_scheduler()
        
        self.scheduler.start()
        logger.info("Scheduler started")
    
    async def stop(self):
        """Para o scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")


# Funcoes de conveniencia

async def run_manual_sync(
    database_url: str,
    api_key: str,
    api_url: str = "https://api.hubquest.com/v1"
) -> SyncResult:
    """Executa sincronizacao manual"""
    config = SyncConfig(
        database_url=database_url,
        api_key=api_key,
        api_url=api_url,
        schedule_day="sunday",  # Not used for manual
        log_to_database=True
    )
    
    job = IncrementalSyncJob(config)
    await job.initialize()
    
    try:
        result = await job.run()
        return result
    finally:
        await job.shutdown()


# CLI Entry Point
if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Incremental Sync Job")
    parser.add_argument("--manual", action="store_true", help="Run manual sync")
    parser.add_argument("--schedule", action="store_true", help="Run scheduler")
    
    args = parser.parse_args()
    
    config = SyncConfig(
        database_url=os.getenv("DATABASE_URL"),
        api_key=os.getenv("HUBQUEST_API_KEY"),
        api_url=os.getenv("HUBQUEST_API_URL", "https://api.hubquest.com/v1"),
        schedule_day=os.getenv("SYNC_SCHEDULE_DAY", "sunday"),
        schedule_time=os.getenv("SYNC_SCHEDULE_TIME", "22:00"),
        state_filter=os.getenv("SYNC_STATE_FILTER", None)
    )
    
    job = IncrementalSyncJob(config)
    
    loop = asyncio.get_event_loop()
    
    try:
        loop.run_until_complete(job.initialize())
        
        if args.manual:
            result = loop.run_until_complete(job.run())
            print(f"Result: {result}")
        elif args.schedule:
            job.setup_scheduler()
            loop.run_until_complete(job.start())
            print("Scheduler running. Press Ctrl+C to stop.")
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                pass
        else:
            # Default: run sync once
            result = loop.run_until_complete(job.run())
            print(f"Result: {result}")
    
    finally:
        loop.run_until_complete(job.shutdown())
