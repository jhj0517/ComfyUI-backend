from pydantic_settings import BaseSettings
import uuid

class Settings(BaseSettings):
    """
    Settings for the backend application.
    If you deployed with docker-compose, make sure to use the correct port for the ComfyUI server.
    """
    COMFY_API_HOST: str = "127.0.0.1"
    COMFY_API_PORT: int = 8188
    COMFY_CLIENT_ID: str = str(uuid.uuid4())  
    
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    TASK_TTL_SECONDS: int = 60*60*24*7  # 7 days
    
    @property
    def COMFY_API_URL(self) -> str:
        return f"http://{self.COMFY_API_HOST}:{self.COMFY_API_PORT}"
        
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

settings = Settings() 