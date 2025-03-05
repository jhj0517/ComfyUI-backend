import os
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Optional, List, Any, Tuple
import mimetypes
import uuid
from urllib.parse import urljoin
import functools

from ..config import settings
from ..logging import get_logger

logger = get_logger()

class S3Service:
    """Service for interacting with AWS S3 for image storage"""
    
    def __init__(self):
        """Initialize the S3 service with AWS credentials from environment variables"""
        self.enabled = settings.S3_STORAGE_ENABLED
        
        if not self.enabled:
            logger.info("S3 storage is disabled, using local URLs")
            return
            
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self.s3_prefix = settings.S3_PREFIX
        
        logger.info(f"S3 service initialized with bucket: {self.bucket_name}")
    
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
            # Return local URL if S3 is disabled
            return {
                "url": image_path,
                "s3_url": None
            }
            
        try:
            filename = os.path.basename(image_path)
            content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            
            s3_key = self._generate_s3_key(filename, subfolder)
            
            self.s3_client.upload_file(
                image_path, 
                self.bucket_name, 
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read' 
                }
            )
            
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            
            if self.cloudfront_enabled and self.cloudfront_domain:
                cloudfront_url = f"https://{self.cloudfront_domain}/{s3_key}"
                url = cloudfront_url
            else:
                url = s3_url
                
            logger.info(f"Successfully uploaded {filename} to S3: {s3_url}")
            
            return {
                "filename": filename,
                "url": url,
                "s3_url": s3_url,
                "s3_key": s3_key
            }
            
        except ClientError as e:
            logger.error(f"Error uploading {image_path} to S3: {e}")
            # Return local URL as fallback
            return {
                "url": image_path,
                "error": str(e)
            }
    
    def process_comfyui_images(self, prompt_id: str, image_data: Dict[str, List[Dict[str, str]]], cleanup: bool = False) -> Dict[str, List[Dict[str, str]]]:
        """
        Process ComfyUI output images - upload them to S3 if enabled.
        
        Args:
            prompt_id: The ComfyUI prompt ID
            image_data: Dictionary of image data from ComfyUI
            cleanup: Whether to cleanup the local file after upload
            
        Returns:
            Modified image data with S3 URLs
        """
        if not self.enabled:
            logger.info("S3 storage disabled, skipping image upload")
            return image_data
            
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