"""
Pytest configuration file for shared fixtures and setup.
Load dotenv file and configure settings.
"""
import os
import sys
import dotenv
import pytest

comfyui_fastapi_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

env_path = os.path.join(comfyui_fastapi_dir, '.env')
dotenv.load_dotenv(env_path)

@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """
    Setup environment for all tests.
    This runs automatically for all tests due to autouse=True.
    """
    from app.config import settings
    
    print("\n=== Test Environment Configuration ===")
    print(f"S3_STORAGE_ENABLED: {settings.S3_STORAGE_ENABLED}")
    print(f"CLOUDFRONT_ENABLED: {settings.CLOUDFRONT_ENABLED}")
    print(f"CLOUDFRONT_SIGNED_URLS_ENABLED: {settings.CLOUDFRONT_SIGNED_URLS_ENABLED}")
    print(f"S3 Bucket: {settings.S3_BUCKET_NAME}")
    print(f"CloudFront Domain: {settings.CLOUDFRONT_DOMAIN}")
    print("=====================================\n")
    
    yield  
