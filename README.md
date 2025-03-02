# ComfyUI backend
Backend for ComfyUI

## Installation & Run
The compose will run both `backend.Dockerfile` and `comfyui.Dockerfile`
```bash
docker compose -f docker/docker-compose.yml up --build
```

The ComfyUI is deployed by default to
```
http://localhost:8188
```

The fastapi server for the ComfyUI is deployed by default to
```
http://localhost:8000
```
Check the swagger UI docs with http://localhost:8000/docs

You can change those ports in `docker/docker-compose.yml`

## Testing (backend)
```bash
cd backend
pytest tests
```



