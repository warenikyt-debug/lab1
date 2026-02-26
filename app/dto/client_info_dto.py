from pydantic import BaseModel

class ClientInfoDTO(BaseModel):
    """
    DTO для информации о клиенте
    """
    ip_address: str
    user_agent: str
    method: str
    requested_url: str
    
    class Config:
        frozen = True