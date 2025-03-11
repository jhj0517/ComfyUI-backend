# ComfyUI backend
fastapi Backend for ComfyUI with AWS S3 and CloudFront integrations. AWS stuffs are optional and only enabled when you setup `.env` file.

## 🛠️ Archictecture
![architecture-2](https://github.com/user-attachments/assets/44456c86-00c1-4e32-b8da-f0d8abb9607e)


## 🐳 Setup with Docker

1. **Git clone repository. Make sure you add `--recursive` at the end to clone submodule together.**
```
git clone https://github.com/jhj0517/ComfyUI-backend.git --recursive
cd ComfyUI-backend
```

2. **(Optional) Setup AWS configs with the `backend/.env`.**

https://github.com/jhj0517/ComfyUI-backend/blob/a66e7750ba9410ddaba6149100a3b8852262a69e/backend/.env.example#L1-L18

3. **(Optional) Setup key files for signed URL with CloudFront.**

  Place your CloudFront key files in `backend/credentials/`:
   - `private_key.pem` 
   - `public_key.pem` 

>[!NOTE]
📝 To create these keys, see [AWS Documentation](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-trusted-signers.html#private-content-creating-cloudfront-key-pairs)

4. **(Optioanl) Setup the Nginx config for your inference server.** 
    
    a. Register your domain name in [`docker/nginx/https.conf`](https://github.com/jhj0517/ComfyUI-backend/blob/master/docker/nginx/https.conf)

    b. Place SSL certificates to [`docker/nginx/ssl/`](https://github.com/jhj0517/ComfyUI-backend/tree/master/docker/nginx/ssl):

>[!NOTE]
📝 To create certificates for your domain name in Windows, see [How to create a "Let's Encrypt" certificate on Windows](https://trueconf.com/blog/knowledge-base/how-to-create-a-lets-encrypt-certificate-on-windows)


5. **Build with the Docker Compose**
```
docker compose -f docker/docker-compose.yml build
```

6. **Run with Docker Compose**
```
docker compose -f docker/docker-compose.yml up
```

7. **Access with**
- ComfyUI: http://localhost:8188 
- FastAPI Backend: http://localhost:8000/docs (or your domain name with nginx)

SwaggerUI is enabled in `/docs` by default, so you can test endpoints there.

## 🧮 ComfyUI Workflows

The default ComfyUI workflow directory for your backend is `backend/workflows/`. 
<br>Place your JSON workflows in the **API compatible** format to use them with the backend.

When you make requests to the `/generate` endpoint, you can modify workflow parameters like this:
#### Example Workflow JSON
```json
{
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["4", 1],
            "text": "masterpiece best quality"
        }
    }
}
```

#### Example API Request
```python
import requests

requests.post(
    "http://localhost:8000/generate",
    data={
        "workflow": "workflow_name",
        "modifications": {
            "6": {
                "text": "Picture of dog smiles"
            }
        }   
    }
)
```

The backend assumes that you have your own proxy server for the client. <br>
So for the sophisticated API parameterization, the proxy server is responsible for it. Or you can just add another endpoint that wraps `/generate` and use it in the fastapi. 

## 🖥️ Device Matching
The backend assumes that you're using Nvidia GPU by default.

If not, edit [`docker/comfyui.Dockerfile`](https://github.com/jhj0517/ComfyUI-backend/blob/master/docker/comfyui.Dockerfile) to match your Device. Update `--extra-index-url` to match your device.

https://github.com/jhj0517/ComfyUI-backend/blob/a66e7750ba9410ddaba6149100a3b8852262a69e/docker/comfyui.Dockerfile#L15-L17

## Misc

Redis db is stored in [`redis-data`](https://github.com/jhj0517/ComfyUI-backend/tree/master/redis-data)<br>
Logs for Nginx is saved in `logs/nginx`
