import os
import logging
from typing import Dict, Optional, List, Any, Tuple
import mimetypes
import uuid
from urllib.parse import urljoin
import functools
import json
import tempfile
import traceback
import datetime
# AWS S3
import boto3
from botocore.exceptions import ClientError
# AWS CloudFront signed URLs
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from botocore.signers import CloudFrontSigner

from ..config import settings
from ..logging import get_logger

logger = get_logger()

class S3Service:
    """Service for interacting with AWS S3 for image storage"""
    
    def __init__(self):
        """Initialize the S3 service with AWS credentials from environment variables"""
        self.enabled = settings.S3_STORAGE_ENABLED
        self.cloudfront_enabled = settings.CLOUDFRONT_ENABLED and settings.CLOUDFRONT_DOMAIN
        
        if not self.enabled:
            logger.warning("S3 storage is disabled, using local URLs")
            return
            
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket_name = settings.S3_BUCKET_NAME
            self.s3_prefix = settings.S3_PREFIX
            logger.info(f"S3 service initialized with bucket: {self.bucket_name}")
            
            # Check CloudFront configuration
            if self.cloudfront_enabled:
                logger.info(f"CloudFront enabled with domain: {settings.CLOUDFRONT_DOMAIN}")
                if settings.CLOUDFRONT_SIGNED_URLS_ENABLED:
                    if not settings.CLOUDFRONT_KEY_PAIR_ID or not settings.CLOUDFRONT_PRIVATE_KEY_PATH:
                        logger.warning("CloudFront signed URLs enabled but missing key configuration")
                    else:
                        logger.info("CloudFront signed URLs enabled")
        except Exception as e:
            logger.error(f"Error connecting to S3, disabling S3 storage: {str(e)}")
            self.enabled = False
            self.cloudfront_enabled = False
    
    def upload_image(self, image_path: str, subfolder: str = None) -> Dict[str, str]:
        """
        Upload an image to S3 and return URLs.
        
        Args:
            image_path: Full path to the image file
            subfolder: Subfolder within the S3 prefix
            
        Returns:
            Dict with URLs for the uploaded image
        """
        if not self.enabled:
            logger.warning("S3 is disabled, returning local URL only")
            # Return local URL if S3 is disabled
            return {
                "url": image_path,
                "s3_url": None
            }
            
        try:
            filename = os.path.basename(image_path)
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            
            if not os.path.exists(image_path):
                return {
                    "url": image_path,
                    "error": f"File does not exist: {image_path}"
                }
            
            file_size = os.path.getsize(image_path)
            
            s3_key = self._generate_s3_key(filename, subfolder)
            
            self.s3_client.upload_file(
                image_path, 
                self.bucket_name, 
                s3_key,
                ExtraArgs={
                    'ContentType': content_type
                }
            )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            
            # Generate CloudFront URL if enabled
            if self.cloudfront_enabled:
                if settings.CLOUDFRONT_SIGNED_URLS_ENABLED:
                    cloudfront_url = self._generate_cloudfront_signed_url(s3_key)
                else:
                    cloudfront_url = f"https://{settings.CLOUDFRONT_DOMAIN}/{s3_key}"
                
                logger.info(f"Generated CloudFront URL for {filename}: {cloudfront_url}")
                
                result = {
                    "filename": filename,
                    "url": cloudfront_url, 
                    "s3_url": s3_url,       
                    "cloudfront_url": cloudfront_url,
                    "s3_key": s3_key
                }
            else:
                logger.info(f"Successfully uploaded {filename} to S3: {s3_url}")
                result = {
                    "filename": filename,
                    "url": s3_url,
                    "s3_url": s3_url,
                    "s3_key": s3_key
                }
                
            return result
            
        except ClientError as e:
            error_message = str(e)
            # Return local URL as fallback
            result = {
                "url": image_path,
                "error": error_message
            }
            logger.warning(f"Returning error result: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            error_message = str(e)
            logger.warning(f"Unexpected error during upload: {error_message}")
            logger.warning(f"Traceback: {traceback.format_exc()}")
            # Return local URL as fallback
            return {
                "url": image_path,
                "error": error_message
            }
    
    def _generate_cloudfront_signed_url(self, s3_key: str) -> str:
        """Generate a signed CloudFront URL for the given S3 key"""
        if not settings.CLOUDFRONT_KEY_PAIR_ID or not settings.CLOUDFRONT_PRIVATE_KEY_PATH:
            logger.warning("CloudFront signed URLs enabled but missing key configuration")
            return f"https://{settings.CLOUDFRONT_DOMAIN}/{s3_key}"
            
        try:            
            def rsa_signer(message):
                with open(settings.CLOUDFRONT_PRIVATE_KEY_PATH, 'rb') as key_file:
                    private_key = load_pem_private_key(
                        key_file.read(),
                        password=None,
                        backend=default_backend()
                    )
                return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())
                
            key_id = settings.CLOUDFRONT_KEY_PAIR_ID
            cf_signer = CloudFrontSigner(key_id, rsa_signer)
            
            # Set expiration time
            expire_date = datetime.datetime.now() + datetime.timedelta(seconds=settings.CLOUDFRONT_URL_EXPIRATION)
            
            # Generate the URL
            url = f"https://{settings.CLOUDFRONT_DOMAIN}/{s3_key}"
            signed_url = cf_signer.generate_presigned_url(
                url,
                date_less_than=expire_date
            )
            
            return signed_url
            
        except Exception as e:
            logger.error(f"Error generating CloudFront signed URL: {e}")
            logger.exception("Detailed error:")
            return f"https://{settings.CLOUDFRONT_DOMAIN}/{s3_key}"
    
    def process_comfyui_images(self, prompt_id: str, image_data: Dict[str, List[Dict[str, str]]], cleanup: Optional[bool] = None) -> Dict[str, List[Dict[str, str]]]:
        """
        Process ComfyUI image data, upload images to S3, and update URLs.
        
        Args:
            prompt_id: The ComfyUI prompt ID
            image_data: Dictionary of image data from ComfyUI
            
        Returns:
            Modified image data with S3 URLs
        """        
        if not self.enabled:
            logger.info("S3 storage disabled, skipping image upload")
            return image_data
        
        if cleanup is None:
            cleanup = settings.LOCAL_IMAGE_CLEANUP_AFTER_UPLOAD
        
        try:
            result = {}
            
            for node_id, images in image_data.items():
                uploaded_images = []
                
                for image in images:
                    if "url" in image:
                        image_url = image["url"]
                        filename = image.get("filename")
                        subfolder = image.get("subfolder")
                        filetype = image.get("type")
                        
                        local_path = self._download_image(image_url, filename)
                        
                        if local_path:
                            s3_data = self.upload_image(local_path, subfolder)
                            
                            image.update({
                                "s3_url": s3_data.get("s3_url"),
                                "url": s3_data.get("url") 
                            })
                            
                            # Cleanup the local file (optional)
                            if cleanup:
                                os.remove(local_path)
                            
                    uploaded_images.append(image)
                
                result[node_id] = uploaded_images
            
            logger.info(f"Processed {sum(len(images) for images in result.values())} images for prompt {prompt_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing images for prompt {prompt_id}: {e}")
            logger.exception("Detailed error")
            # Return original data as fallback
            return image_data
    
    def _generate_s3_key(self, filename: str, subfolder: str = None) -> str:
        """Generate a unique S3 key for the image"""
        from datetime import datetime
        
        date_prefix = datetime.now().strftime("%Y-%m-%d")
        unique_id = str(uuid.uuid4())[:8]
        
        if subfolder:
            return f"{self.s3_prefix}{date_prefix}/{subfolder}/{unique_id}_{filename}"
        else:
            return f"{self.s3_prefix}{date_prefix}/{unique_id}_{filename}"
    
    def _download_image(self, url: str, filename: str) -> Optional[str]:
        """Download an image from URL to local temporary storage"""
        import tempfile
        import urllib.request
        
        try:
            temp_dir = tempfile.gettempdir()
            local_path = os.path.join(temp_dir, filename)
            
            urllib.request.urlretrieve(url, local_path)
            
            return local_path
        except Exception as e:
            logger.error(f"Error downloading image {filename} from {url}: {e}")
            return None

@functools.lru_cache(maxsize=1)
def get_s3_service() -> S3Service:
    """
    Get or create S3Service singleton instance.
    
    Returns:
        S3Service: The singleton instance
    """
    return S3Service() 