# ComfyUI backend
Backend for ComfyUI

## Archictecture
(ComfyUI <-> ComfyUI-fastapi-Wrapper) <-  Reverse Proxy (API) <- Your Front End

## Installation & Run
The compose will run both `backend.Dockerfile` and `comfyui.Dockerfile`
```bash
docker compose -f docker/docker-compose.yml up --build
```
When running the container, just remove `--build` at the end.

And when you made changes to backend and re-build backend only, do:
```bash
docker compose -f docker/docker-compose.yml build backend
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

+) If you want to test them locally, you can use requirements-cuda.txt or requirements-cuda.txt

## Workflows

The workflows are placed in backend/workflows.
And the workflow must be **API compatible** format.


## Testing (backend)
```bash
cd backend
pytest tests
```



