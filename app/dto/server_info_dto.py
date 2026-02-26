from pydantic import BaseModel

class ServerInfoDTO(BaseModel):
    """
    DTO для информации о сервере
    """
    php_version: str
    server_software: str
    server_name: str
    server_port: int
    document_root: str
    
    class Config:
        frozen = True 