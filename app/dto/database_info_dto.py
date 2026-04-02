from pydantic import BaseModel

class DatabaseInfoDTO(BaseModel):
    """
    DTO для информации о базе данных
    """
    database_name: str
    connection_status: str
    
    class Config:
        frozen = True