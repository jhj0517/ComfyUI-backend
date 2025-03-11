# ComfyUI backend
fastapi Backend for ComfyUI with AWS S3 and CloudFront integrations. AWS stuffs are optional and only enabled when you setup `.env` file.

## Archictecture
[picture]

## Setup with Docker

1. Git clone repository
```
git clone https://github.com/jhj0517/ComfyUI-backend.git --recursive
cd ComfyUI-backend
```
Make sure you add `--recursive` at the end to clone the ComfyUI submodule as well.

2. (Optional) Setup `.env` file in `backend/.env`.
```
# AWS S3 Configuration
S3_STORAGE_ENABLED=true
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
S3_PREFIX=images/
LOCAL_IMAGE_CLEANUP_AFTER_UPLOAD=false

# CloudFront Configuration
CLOUDFRONT_ENABLED=true
CLOUDFRONT_DOMAIN=your-distribution.cloudfront.net
CLOUDFRONT_SIGNED_URLS_ENABLED=true
CLOUDFRONT_KEY_PAIR_ID=your_key_pair_id
CLOUDFRONT_PRIVATE_KEY_PATH=/app/credentials/private_key.pem
CLOUDFRONT_URL_EXPIRATION=86400
```

3. (Optional) Setup key files for signed URL with CloudFront.

  Place your CloudFront key files in `backend/credentials/`:
   - `private_key.pem` 
   - `public_key.pem` 

>  📝 To create these keys, see [AWS Documentation](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-trusted-signers.html#private-content-creating-cloudfront-key-pairs)

4. (Optioanl) Setup the Nginx config for your inference server's domain name. 
    
    a. Register your domain name in `docker/nginx/https.conf`

    b. Place SSL certificates to `docker/nginx/ssl/`:

> 📝 To create certificates for your domain name in Windows, see [How to create a “Let’s Encrypt” certificate on Windows](https://trueconf.com/blog/knowledge-base/how-to-create-a-lets-encrypt-certificate-on-windows)


5. Build with the Docker Compose
```
docker compose -f docker/docker-compose.yml build
```

6. Run with Docker Compose
```
docker compose -f docker/docker-compose.yml up
```

7. Access with
- ComfyUI: http://localhost:8188 
- FastAPI Backend: http://localhost:8000/docs (or your domain name with nginx)

SwaggerUI is enabled in `/docs` by default, so you can test endpoints there.

## ComfyUI Workflows





