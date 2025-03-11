from pydantic_settings import BaseSettings, SettingsConfigDict
import uuid
import os
from typing import Optional


comfyui_fastapi_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOTENV = os.path.join(comfyui_fastapi_root, ".env")

class Settings(BaseSettings):
    """
    Settings for the backend application.
    If you deployed with docker-compose, make sure to use the correct port for the ComfyUI server.
    Some settings (e.g. AWS S3) are overridden by the dotenv file.
    """
    # ComfyUI Configuration
    COMFY_API_HOST: str = os.getenv("COMFY_API_HOST", "127.0.0.1")
    COMFY_API_PORT: int = int(os.getenv("COMFY_API_PORT", "8188"))
    COMFY_CLIENT_ID: str = str(uuid.uuid4())  
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    TASK_TTL_SECONDS: int = int(os.getenv("TASK_TTL_SECONDS", str(60*60*24*7)))  # 7 days default
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str =  os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: Optional[str] = None
    S3_PREFIX: str = os.getenv("S3_PREFIX", "images/")
    S3_STORAGE_ENABLED: bool = False
    LOCAL_IMAGE_CLEANUP_AFTER_UPLOAD: bool = False  # Whether to delete local temporary files after upload
    
    # CloudFront Configuration
    CLOUDFRONT_ENABLED: bool = False
    CLOUDFRONT_DOMAIN: Optional[str] = None  # e.g., "d1234abcdef.cloudfront.net" or "assets.yourdomain.com"
    CLOUDFRONT_KEY_PAIR_ID: Optional[str] = None  # For signed URL
    CLOUDFRONT_PRIVATE_KEY_PATH: Optional[str] = None  # For signed URL
    CLOUDFRONT_SIGNED_URLS_ENABLED: bool = False  # Whether to use signed URL
    CLOUDFRONT_URL_EXPIRATION: int = 604800  # Signed URL expiration date, 7 days by default

    # Proxy Server Webhook Configuration
    PROXY_WEBHOOK_URL: str = os.getenv("PROXY_WEBHOOK_URL", "")
    PROXY_WEBHOOK_SECRET: str = os.getenv("PROXY_WEBHOOK_SECRET", "")
    
    @property
    def COMFY_API_URL(self) -> str:
        return f"http://{self.COMFY_API_HOST}:{self.COMFY_API_PORT}"
        
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Dotenv file manages S3 configuration. The AWS configs will be overridden by the dotenv file.
    model_config = SettingsConfigDict(
        env_file=DOTENV,
        env_file_encoding="utf-8"
    )

settings = Settings() 