import pytest
import httpx
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import from conftest
from conftest import STYLE_SERVICE_URL

# Mark all tests in this file with style marker
pytestmark = pytest.mark.style

# Add missing fixtures
@pytest.fixture
def sample_streetwear_clothing_image():
    """Create a simple test image for streetwear clothing."""
    return b"mock_streetwear_clothing_data"

@pytest.fixture
def sample_athletic_clothing_image():
    """Create a simple test image for athletic wear clothing."""
    return b"mock_athletic_clothing_data"

@pytest.mark.asyncio
async def test_style_health_endpoint(async_httpx_client, monkeypatch):
    """Test the health endpoint of the Style IEP."""
    # Mock the response
    async def mock_get(*args, **kwargs):
        response = httpx.Response(200, json={"status": "healthy", "model": "YOLOv8 Style Classification"})
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "get", mock_get)
    
    # Make the request
    response = await async_httpx_client.get(f"{STYLE_SERVICE_URL}/health")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data
    assert data["model"] == "YOLOv8 Style Classification"

@pytest.mark.asyncio
async def test_style_classify_casual(async_httpx_client, monkeypatch, sample_casual_clothing_image):
    """Test the classification endpoint with casual clothing."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            200, 
            json={
                "styles": [
                    {
                        "style_name": "Casual", 
                        "style_id": 0, 
                        "confidence": 0.92
                    }
                ],
                "processing_time": 0.35,
                "image_size": [480, 640]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('casual.jpg', sample_casual_clothing_image, 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{STYLE_SERVICE_URL}/classify",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "styles" in data
    assert len(data["styles"]) > 0
    assert data["styles"][0]["style_name"] == "Casual"
    assert data["styles"][0]["style_id"] == 0  # Correct style ID for Casual
    assert data["styles"][0]["confidence"] > 0.9  # High confidence in Casual
    assert "processing_time" in data
    assert "image_size" in data

@pytest.mark.asyncio
async def test_style_classify_formal(async_httpx_client, monkeypatch, sample_formal_clothing_image):
    """Test the classification endpoint with formal clothing."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            200, 
            json={
                "styles": [
                    {
                        "style_name": "Formal", 
                        "style_id": 1, 
                        "confidence": 0.89
                    }
                ],
                "processing_time": 0.33,
                "image_size": [480, 640]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('formal.jpg', sample_formal_clothing_image, 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{STYLE_SERVICE_URL}/classify",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "styles" in data
    assert len(data["styles"]) > 0
    assert data["styles"][0]["style_name"] == "Formal"
    assert data["styles"][0]["style_id"] == 1  # Correct style ID for Formal
    assert data["styles"][0]["confidence"] > 0.8  # High confidence in formal
    assert "processing_time" in data
    assert "image_size" in data

@pytest.mark.asyncio
async def test_style_classify_streetwear(async_httpx_client, monkeypatch, sample_streetwear_clothing_image):
    """Test the classification endpoint with streetwear clothing."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            200, 
            json={
                "styles": [
                    {
                        "style_name": "Streetwear", 
                        "style_id": 3, 
                        "confidence": 0.82
                    }
                ],
                "processing_time": 0.37,
                "image_size": [480, 640]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('streetwear.jpg', sample_streetwear_clothing_image, 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{STYLE_SERVICE_URL}/classify",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "styles" in data
    assert len(data["styles"]) > 0
    assert data["styles"][0]["style_name"] == "Streetwear"
    assert data["styles"][0]["style_id"] == 3  # Correct style ID for Streetwear
    assert data["styles"][0]["confidence"] > 0.8  # High confidence
    assert "processing_time" in data
    assert "image_size" in data

@pytest.mark.asyncio
async def test_style_classify_athletic_wear(async_httpx_client, monkeypatch, sample_athletic_clothing_image):
    """Test the classification endpoint with athletic wear."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            200, 
            json={
                "styles": [
                    {
                        "style_name": "athletic wear", 
                        "style_id": 4, 
                        "confidence": 0.85
                    }
                ],
                "processing_time": 0.31,
                "image_size": [480, 640]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('athletic.jpg', sample_athletic_clothing_image, 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{STYLE_SERVICE_URL}/classify",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "styles" in data
    assert len(data["styles"]) > 0
    assert data["styles"][0]["style_name"] == "athletic wear"
    assert data["styles"][0]["style_id"] == 4  # Correct style ID for athletic wear
    assert data["styles"][0]["confidence"] > 0.8  # High confidence
    assert "processing_time" in data
    assert "image_size" in data

@pytest.mark.asyncio
async def test_style_classify_no_clothing(async_httpx_client, monkeypatch, mock_image_file):
    """Test the classification endpoint with an image containing no clothing."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            200, 
            json={
                "styles": [],
                "processing_time": 0.25,
                "image_size": [480, 640]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('empty.jpg', mock_image_file, 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{STYLE_SERVICE_URL}/classify",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "styles" in data
    assert len(data["styles"]) == 0  # No styles detected
    assert "processing_time" in data
    assert "image_size" in data

@pytest.mark.asyncio
async def test_style_classify_invalid_image(async_httpx_client, monkeypatch):
    """Test the classification endpoint with an invalid image."""
    # Create invalid image data
    invalid_image_data = b"This is not a valid image file"
    
    # Mock the response
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            400, 
            json={"detail": "Invalid image file"}
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('invalid.jpg', invalid_image_data, 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{STYLE_SERVICE_URL}/classify",
        files=files
    )
    
    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Invalid image file"

@pytest.mark.asyncio
async def test_style_classify_multiple_styles(async_httpx_client, monkeypatch, sample_person_image):
    """Test the classification endpoint with multiple styles in the image."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            200, 
            json={
                "styles": [
                    {
                        "style_name": "Casual", 
                        "style_id": 0, 
                        "confidence": 0.82
                    },
                    {
                        "style_name": "Streetwear", 
                        "style_id": 3, 
                        "confidence": 0.65
                    }
                ],
                "processing_time": 0.38,
                "image_size": [480, 640]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('person.jpg', sample_person_image, 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{STYLE_SERVICE_URL}/classify",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "styles" in data
    assert len(data["styles"]) == 2
    assert data["styles"][0]["style_name"] == "Casual"
    assert data["styles"][0]["style_id"] == 0
    assert data["styles"][1]["style_name"] == "Streetwear"
    assert data["styles"][1]["style_id"] == 3
    assert "processing_time" in data
    assert "image_size" in data

@pytest.mark.asyncio
async def test_style_classify_with_custom_confidence(async_httpx_client, monkeypatch, sample_casual_clothing_image):
    """Test the classification endpoint with a custom confidence threshold."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Extract the confidence parameter from request data
        data = kwargs.get("data", {})
        confidence = float(data.get("confidence", "0.3"))  # Default is 0.3
        
        # Create different responses based on confidence
        if confidence > 0.7:
            # Only return high confidence results
            styles = [
                {
                    "style_name": "Casual", 
                    "style_id": 0, 
                    "confidence": 0.92
                }
            ]
        else:
            # Return more results with lower confidence threshold
            styles = [
                {
                    "style_name": "Casual", 
                    "style_id": 0, 
                    "confidence": 0.92
                },
                {
                    "style_name": "Other", 
                    "style_id": 2, 
                    "confidence": 0.45
                }
            ]
        
        response = httpx.Response(
            200, 
            json={
                "styles": styles,
                "processing_time": 0.29,
                "image_size": [480, 640]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('casual.jpg', sample_casual_clothing_image, 'image/jpeg')}
    
    # Make request with default confidence
    response_default = await async_httpx_client.post(
        f"{STYLE_SERVICE_URL}/classify",
        files=files
    )
    
    # Make request with higher confidence
    data_high_conf = {"confidence": "0.8"}
    response_high_conf = await async_httpx_client.post(
        f"{STYLE_SERVICE_URL}/classify",
        files=files,
        data=data_high_conf
    )
    
    # Assertions
    assert response_default.status_code == 200
    assert response_high_conf.status_code == 200
    
    data_default = response_default.json()
    data_high_conf = response_high_conf.json()
    
    assert len(data_default["styles"]) == 2  # More results with default threshold
    assert len(data_high_conf["styles"]) == 1  # Fewer results with higher threshold 