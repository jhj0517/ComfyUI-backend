#!/usr/bin/env python
"""
Test script for S3 integration.
Run with: python -m app.tests.test_s3_upload
"""

import os
import sys
import logging
from dotenv import load_dotenv
import tempfile

#  Use the .env file in the root of the backend directory
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
dotenv_path = os.path.join(backend_root, ".env")

from app.services.s3_service import get_s3_service

logger = logging.getLogger()

def create_test_image():
    """Create a simple test image"""
    from PIL import Image
    
    temp_dir = tempfile.gettempdir()
    test_image_path = os.path.join(temp_dir, "test_s3_upload.png")
    
    # Create a simple image
    img = Image.new('RGB', (100, 100), color = (73, 109, 137))
    img.save(test_image_path)
    
    logger.info(f"Created test image at {test_image_path}")
    return test_image_path

def test_s3_upload():
    """Test uploading to S3"""
    load_dotenv(dotenv_path)
    
    # Check if S3 is configured
    s3_enabled = os.getenv('S3_STORAGE_ENABLED', 'false').lower() == 'true'
    if not s3_enabled:
        logger.warning("S3 storage is disabled. Set S3_STORAGE_ENABLED=true to enable.")
        logger.info("Continuing test with S3 storage explicitly enabled for testing...")
    
    s3_service = get_s3_service()
    
    test_image_path = create_test_image()

    original_enabled = s3_service.enabled
    s3_service.enabled = True
    
    # Upload the test image
    logger.info("Testing S3 upload...")
    result = s3_service.upload_image(test_image_path, "test")
    
    assert "error" not in result, f"Upload failed: {result.get('error')}"
    
    assert "s3_url" in result, "S3 URL not found in result"
    assert result["s3_url"].startswith(f"https://{s3_service.bucket_name}.s3.amazonaws.com/"), "S3 URL has incorrect format"
    assert "s3_key" in result, "S3 key not found in result"
    
    logger.info(f"Upload successful!")
    logger.info(f"S3 URL: {result['s3_url']}")
    logger.info(f"Public URL: {result['url']}")
    
    # Reset the enabled state
    s3_service.enabled = original_enabled
    
    # Clean up test image
    try:
        os.remove(test_image_path)
    except:
        pass
