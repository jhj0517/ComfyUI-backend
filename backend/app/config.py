from pydantic_settings import BaseSettings
import uuid
import os
from typing import Optional

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
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    S3_PREFIX: str = "images/"
    S3_STORAGE_ENABLED: bool = False
    
    @property
    def COMFY_API_URL(self) -> str:
        return f"http://{self.COMFY_API_HOST}:{self.COMFY_API_PORT}"
        
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        """
        This automatically loads .env file and registers environment variables with pydantic.
        """
        backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        env_file = os.path.join(backend_root, ".env")
        env_file_encoding = "utf-8"

settings = Settings() 