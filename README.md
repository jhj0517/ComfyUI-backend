# ComfyUI backend
Backend for ComfyUI

## Installation & Run
The compose will run both `backend.Dockerfile` and `comfyui.Dockerfile`
```bash
docker compose -f docker/docker-compose.yml up --build
```

## Testing (backend)
```bash
cd backend
pytest tests
```



