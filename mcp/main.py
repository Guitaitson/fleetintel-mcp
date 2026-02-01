from fastapi import FastAPI, Header, HTTPException
import asyncio
from mcp.jobs.incremental_sync import run_incremental_sync
import os

app = FastAPI()

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "default-secret-key")

@app.post("/admin/sync/trigger")
async def trigger_sync_manually(api_key: str = Header(None, alias="api-key")):
    """Endpoint para acionamento manual da sincronização"""
    if api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="API key inválida"
        )
    
    # Executar em segundo plano
    asyncio.create_task(run_incremental_sync())
    
    return {
        "status": "sincronização iniciada em background",
        "message": "Verifique os logs para acompanhar o progresso"
    }

@app.get("/")
async def health_check():
    return {"status": "active", "service": "fleetintel-mpc"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
