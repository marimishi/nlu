from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import AsyncIterator

from api.routes import router
from config.model_config import ModelConfig
from core.nlu.services.nlu_service import NLUService
from core.command.processor import CommandProcessor
from core.registry.registry_service import RegistryService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan контекст для управления жизненным циклом приложения"""
    # Startup
    try:
        print("Initializing services...")
        registry_service = RegistryService()
        processor = CommandProcessor(registry_service)
        nlu_service = NLUService()
        
        # Сохраняем сервисы в состоянии приложения
        app.state.registry_service = registry_service
        app.state.processor = processor
        app.state.nlu_service = nlu_service
        
        print("NLU Service started successfully")
    except Exception as e:
        print(f"Error initializing services: {e}")
        app.state.registry_service = None
        app.state.processor = None
        app.state.nlu_service = None
    
    yield
    
    print("Shutting down NLU Service...")


def create_app() -> FastAPI:
    app = FastAPI(
        title=ModelConfig.APP_NAME,
        description=ModelConfig.APP_DESCRIPTION,
        version="1.0.0",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=ModelConfig.HOST,
        port=ModelConfig.PORT,
        reload=ModelConfig.DEBUG,
        log_level="info"
    )