from fastapi import FastAPI
from .routers import generation, workflows, system

app = FastAPI(title="ComfyUI API Wrapper", 
              description="API for interacting with ComfyUI workflows",
              version="0.1.0")

app.include_router(generation.router)
app.include_router(workflows.router)
app.include_router(system.router)

@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "message": "Welcome to ComfyUI API Wrapper",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    } 