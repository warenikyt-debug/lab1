from pydantic import BaseModel

class DatabaseInfoDTO(BaseModel):
    """
    DTO для информации о базе данных
    """
    driver: str
    database_name: str
    server_version: str
    connection_status: str
    
    class Config:
        frozen = True