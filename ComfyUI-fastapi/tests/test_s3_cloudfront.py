"""
Test S3 uploads and CloudFront signed URLs using pytest.
"""
import os
import pytest
import tempfile
import requests
from PIL import Image
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

# Import settings and s3_service after environment is loaded in conftest.py
from app.config import settings
from app.services.s3_service import get_s3_service


@pytest.fixture(scope="module")
def s3_service():
    """Initialize and return the S3 service"""
    service = get_s3_service()
    return service


@pytest.fixture(scope="module")
def test_image():
    """Create a test image and return its path"""
    temp_dir = tempfile.gettempdir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_s3_cf_{timestamp}.png"
    filepath = os.path.join(temp_dir, filename)
    
    # Create a simple colored image
    img = Image.new('RGB', (200, 200), color=(73, 109, 137))
    img.save(filepath)
    
    print(f"Created test image: {filepath}")
    yield filepath
    
    # Cleanup after tests
    if os.path.exists(filepath):
        os.remove(filepath)
        print(f"Cleaned up test image: {filepath}")


@pytest.mark.skipif(not settings.S3_STORAGE_ENABLED, 
                   reason="S3 storage is disabled")
def test_s3_upload(s3_service, test_image):
    """Test uploading an image to S3"""
    # Upload the image
    result = s3_service.upload_image(test_image, "test")
    
    # Check basic result properties
    assert "error" not in result, f"Upload error: {result.get('error')}"
    assert "s3_url" in result, "S3 URL not returned"
    assert "s3_key" in result, "S3 key not returned"
    assert result["s3_url"].startswith(f"https://{settings.S3_BUCKET_NAME}.s3"), "Incorrect S3 URL format"
    
    s3_url = result["s3_url"]
    parsed_url = urlparse(s3_url)
    assert parsed_url.scheme == "https", "S3 URL should use HTTPS"
    assert settings.S3_BUCKET_NAME in parsed_url.netloc, "S3 URL should contain bucket name"


@pytest.mark.skipif(not (settings.S3_STORAGE_ENABLED and settings.CLOUDFRONT_ENABLED), 
                   reason="S3 storage or CloudFront is disabled")
def test_cloudfront_url_generation(s3_service, test_image):
    """Test CloudFront URL generation"""
    # Upload image to get CloudFront URL
    result = s3_service.upload_image(test_image, "test")
    
    cloudfront_url = result["cloudfront_url"]
    parsed_url = urlparse(cloudfront_url)
    assert parsed_url.scheme == "https", "CloudFront URL should use HTTPS"
    assert parsed_url.netloc == settings.CLOUDFRONT_DOMAIN, "CloudFront URL has incorrect domain"


@pytest.mark.skipif(not (settings.S3_STORAGE_ENABLED and 
                       settings.CLOUDFRONT_ENABLED and 
                       settings.CLOUDFRONT_SIGNED_URLS_ENABLED),
                   reason="S3, CloudFront, or signed URLs are disabled")
def test_cloudfront_signed_url(s3_service, test_image):
    """Test CloudFront signed URL generation and verification"""
    # Upload image to get signed CloudFront URL
    result = s3_service.upload_image(test_image, "test")
    
    cloudfront_url = result["cloudfront_url"]
    parsed_url = urlparse(cloudfront_url)
    query_params = parse_qs(parsed_url.query)
    
    assert "Expires" in query_params, "Missing Expires parameter in signed URL"
    assert "Signature" in query_params, "Missing Signature parameter in signed URL"
    assert "Key-Pair-Id" in query_params, "Missing Key-Pair-Id parameter in signed URL"
    
    # Verify expiration
    expires_timestamp = int(query_params["Expires"][0])
    expires_date = datetime.fromtimestamp(expires_timestamp)
    now = datetime.now()
    
    assert expires_date > now, "Signed URL has already expired"
    
    expected_expiry = now + timedelta(seconds=settings.CLOUDFRONT_URL_EXPIRATION)
    margin = timedelta(days=1)  
    time_diff = abs(expires_date - expected_expiry)

    assert time_diff <= margin, f"Expiration time differs by {time_diff}, which exceeds margin of {margin}. This might be due to timezone differences or AWS SDK behavior."

@pytest.mark.skipif(not (settings.S3_STORAGE_ENABLED and settings.CLOUDFRONT_ENABLED), 
                   reason="S3 storage or CloudFront is disabled")
def test_cloudfront_accessibility(s3_service, test_image):
    """Test if CloudFront URL is accessible (optional)"""
    # Skip actual HTTP request if in CI environment
    if os.environ.get("CI") == "true":
        pytest.skip("Skipping network request in CI environment")
    
    result = s3_service.upload_image(test_image, "test")
    cloudfront_url = result["cloudfront_url"]
    
    try:
        response = requests.get(cloudfront_url, timeout=10)
        assert response.status_code == 200, f"CloudFront URL not accessible: {response.status_code}"
        
        content_type = response.headers.get("Content-Type")
        assert "image" in content_type.lower(), f"Unexpected content type: {content_type}"
        
    except requests.RequestException as e:
        pytest.skip(f"Network error during CloudFront test: {e}") 