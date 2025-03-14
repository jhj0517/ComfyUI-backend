# ComfyUI backend
A fastapi backend for ComfyUI with AWS S3 and CloudFront integration. The AWS stuffs are completely optional and only enabled when you setup `.env` file.

## 🛠️ Archictecture
![architecture-3](https://github.com/user-attachments/assets/88d916c8-84cf-4cec-abc0-aee75ef9f874)


## 🐳 Setup with Docker Compose

1. **Git clone repository. Make sure you add `--recursive` at the end to clone submodule together.**
```
git clone https://github.com/jhj0517/ComfyUI-backend.git --recursive
cd ComfyUI-backend
```

2. **(Optional) Setup AWS configs in the `ComfyUI-fastapi/.env`.**

https://github.com/jhj0517/ComfyUI-backend/blob/859559f3cee6202a691c6424a59eb5372a29fb10/ComfyUI-fastapi/.env.example#L1-L22

3. **(Optional) Setup key files for signed URL with CloudFront.**

  Place your CloudFront key files in [`ComfyUI-fastapi/credentials/`](https://github.com/jhj0517/ComfyUI-backend/tree/master/ComfyUI-fastapi/credentials):
   - `private_key.pem` 
   - `public_key.pem` 

>[!NOTE]
📝 To create these keys, see [AWS Documentation](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-trusted-signers.html#private-content-creating-cloudfront-key-pairs)

4. **(Optioanl) Setup the Nginx config for your inference server.** 
    
    1. Register your domain name in [`docker/nginx/https.conf`](https://github.com/jhj0517/ComfyUI-backend/blob/master/docker/nginx/https.conf)

    2. Place SSL certificates to [`docker/nginx/ssl/`](https://github.com/jhj0517/ComfyUI-backend/tree/master/docker/nginx/ssl):
       - `fullchain.pem`
       - `privkey.pem`

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

7. **Access, Test with**
- ComfyUI: http://localhost:8188 
- FastAPI Backend: http://localhost:8000/docs (or your domain name with nginx)

SwaggerUI is enabled in `/docs` by default, so you can test endpoints there.

## 🧮 ComfyUI Workflows

The default ComfyUI workflow directory for your backend is [`ComfyUI-fastapi/workflows/`](https://github.com/jhj0517/ComfyUI-backend/tree/master/ComfyUI-fastapi/workflows). 
<br>Place your JSON workflows in the **API compatible** format to use them with the backend.

When you make requests to the `/generation` endpoint, you can modify workflow parameters like this:
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
        "workflow_name": "sdxl_t2i",
        "modifications": {
            "6": {
                "text": "Picture of dog smiles"
            }
        }   
    }
)
```

The backend assumes that you have your own proxy server for the client. <br>
So for the sophisticated API parameterization, the proxy server is responsible for it.<br>
This provides several advantages, including flexibility for workflows in the inference server. <br>
Or you can just add another endpoint that wraps `/generation` and use it in the fastapi. 

## 🖥️ Device Matching
The backend assumes that you're using Nvidia GPU by default.

If not, edit [`docker/comfyui.Dockerfile`](https://github.com/jhj0517/ComfyUI-backend/blob/master/docker/comfyui.Dockerfile) to match your Device. Update `--extra-index-url` to match your device.

https://github.com/jhj0517/ComfyUI-backend/blob/a66e7750ba9410ddaba6149100a3b8852262a69e/docker/comfyui.Dockerfile#L15-L17

## 📦 Installing Custom Nodes

The custom nodes directory is mapped as volume to `ComfyUI/custom_nodes` in the container.

To install custom nodes:
1. Add your custom node to the `ComfyUI/custom_nodes` directory
2. Add required dependencies for custom node to `ComfyUI/requirements.txt`
3. Rebuild the ComfyUI container:
```bash
docker compose -f docker/docker-compose.yml build comfyui
```

After rebuilding, your custom nodes will be available in ComfyUI!

## 📚 Misc

Redis db is stored in [`redis-data/`](https://github.com/jhj0517/ComfyUI-backend/tree/master/redis-data)<br>
Logs for Nginx is saved in `logs/nginx/`
