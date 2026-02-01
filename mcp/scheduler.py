import schedule
import asyncio
from jobs.incremental_sync import run_incremental_sync
import os

async def scheduled_sync():
    """Executa a sincronização incremental agendada"""
    print(f"🚀 Iniciando sincronização agendada em {datetime.now()}")
    await run_incremental_sync()

# Configurar agendamento baseado em variáveis de ambiente
schedule_day = os.getenv("SYNC_SCHEDULE_DAY", "sunday").lower()
schedule_time = os.getenv("SYNC_SCHEDULE_TIME", "22:00")

# Mapear dias da semana
schedule_map = {
    "monday": schedule.every().monday,
    "tuesday": schedule.every().tuesday,
    "wednesday": schedule.every().wednesday,
    "thursday": schedule.every().thursday,
    "friday": schedule.every().friday,
    "saturday": schedule.every().saturday,
    "sunday": schedule.every().sunday
}

# Registrar tarefa agendada
if schedule_day in schedule_map:
    schedule_map[schedule_day].at(schedule_time).do(
        lambda: asyncio.create_task(scheduled_sync())
    )
else:
    raise ValueError(f"Dia de agendamento inválido: {schedule_day}")

# Loop principal do scheduler
async def run_scheduler():
    """Executa o loop principal do agendador"""
    print(f"⏰ Scheduler iniciado. Próxima execução: {schedule_day} às {schedule_time}")
    while True:
        schedule.run_pending()
        await asyncio.sleep(60)  # Verificar a cada minuto

if __name__ == "__main__":
    asyncio.run(run_scheduler())
