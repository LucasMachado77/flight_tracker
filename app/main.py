"""Aplicação FastAPI principal"""
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import create_tables
from app.api.routes import router as route_watches_router
from app.jobs.background_scheduler import BackgroundScheduler

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Scheduler global
scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    global scheduler
    
    # Startup
    logging.info(f"Iniciando {settings.app_name} v{settings.app_version}")
    create_tables()
    logging.info("Tabelas do banco de dados criadas/verificadas")
    
    # Iniciar scheduler em background
    scheduler = BackgroundScheduler()
    await scheduler.start()
    logging.info("Scheduler de background iniciado")
    
    yield
    
    # Shutdown
    if scheduler:
        await scheduler.stop()
        logging.info("Scheduler de background parado")

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Sistema de rastreamento de preços de passagens aéreas",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos (frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções"""
    logging.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"}
    )


@app.get("/")
async def root():
    """Endpoint raiz - redireciona para o frontend"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")


@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    global scheduler
    scheduler_status = "running" if scheduler and scheduler.is_running else "stopped"
    return {
        "status": "healthy",
        "scheduler": scheduler_status
    }


# Registrar routers
app.include_router(route_watches_router)


@app.post("/admin/force-check")
async def force_price_check():
    """Forçar verificação de todas as rotas ativas"""
    global scheduler
    if not scheduler:
        return {"error": "Scheduler não disponível"}
    
    result = await scheduler.force_check_all()
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)