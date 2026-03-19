from fastapi import APIRouter, Request
import sys
import socket
import os
from ..dto.server_info_dto import ServerInfoDTO
from ..dto.client_info_dto import ClientInfoDTO
from ..dto.database_info_dto import DatabaseInfoDTO
from ..config.settings import settings

router = APIRouter(prefix="/info", tags=["info"])

def get_fastapi_version():
    import fastapi
    return fastapi.__version__

@router.get("/server", response_model=ServerInfoDTO)
async def server_info():
    return ServerInfoDTO(
        php_version=f"Python {sys.version.split()[0]}",
        server_software=f"FastAPI/{get_fastapi_version()}",
        server_name=socket.gethostname(),
        server_port=int(os.getenv("PORT", 8000)),
        document_root=os.getcwd()
    )

@router.get("/client", response_model=ClientInfoDTO)
async def client_info(request: Request):
    return ClientInfoDTO(
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        method=request.method,
        requested_url=str(request.url)
    )

@router.get("/database", response_model=DatabaseInfoDTO)
async def database_info():
    # Простая заглушка без БД
    return DatabaseInfoDTO(
        driver=settings.DATABASE_DRIVER,
        database_name=settings.DATABASE_NAME,
        server_version="SQLite",
        connection_status="connected"
    )