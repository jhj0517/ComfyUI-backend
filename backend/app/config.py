from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    COMFY_API_HOST: str = "127.0.0.1"
    COMFY_API_PORT: int = 8188
    
    @property
    def COMFY_API_URL(self) -> str:
        return f"http://{self.COMFY_API_HOST}:{self.COMFY_API_PORT}"

settings = Settings() 

class WorkflowNotFoundError(Exception):
    pass

class WorkflowValidationError(Exception):
    pass 