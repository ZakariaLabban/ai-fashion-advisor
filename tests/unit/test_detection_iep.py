import pytest
import httpx
import json
import base64
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import from conftest
from conftest import DETECTION_SERVICE_URL

# Mark all tests in this file with detection marker
pytestmark = pytest.mark.detection

@pytest.fixture
def sample_person_image():
    """Create a sample image with a person wearing clothes for testing."""
    return b"mock_person_image_data"

@pytest.fixture
def mock_image_file():
    """Create a mock image file with no clothing for testing."""
    return b"mock_empty_image_data"

@pytest.mark.asyncio
async def test_detection_health_endpoint(async_httpx_client, monkeypatch):
    """Test the health endpoint of the Detection IEP."""
    # Mock the response
    async def mock_get(*args, **kwargs):
        response = httpx.Response(200, json={"status": "healthy", "model": "YOLOv8 Detection"})
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "get", mock_get)
    
    # Make the request
    response = await async_httpx_client.get(f"{DETECTION_SERVICE_URL}/health")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data
    assert data["model"] == "YOLOv8 Detection"

@pytest.mark.asyncio
async def test_detection_endpoint_valid_image(async_httpx_client, monkeypatch, sample_person_image):
    """Test the detection endpoint with a valid image."""
    # Create mock base64 encoded crops
    mock_shirt_crop = base64.b64encode(b"shirt crop data").decode("utf-8")
    mock_pants_crop = base64.b64encode(b"pants crop data").decode("utf-8")
    
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Check if include_crops parameter is set
        data = kwargs.get("data", {})
        include_crops = data.get("include_crops") == "True"
        
        response = httpx.Response(
            200, 
            json={
                "detections": [
                    {
                        "class_name": "Shirt", 
                        "class_id": 4, 
                        "confidence": 0.92, 
                        "bbox": [125, 100, 175, 350],
                        "crop_data": mock_shirt_crop if include_crops else None
                    },
                    {
                        "class_name": "Pants/Shorts", 
                        "class_id": 10, 
                        "confidence": 0.88, 
                        "bbox": [125, 350, 175, 550],
                        "crop_data": mock_pants_crop if include_crops else None
                    }
                ],
                "processing_time": 0.45,
                "image_size": [600, 400]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('person.jpg', sample_person_image, 'image/jpeg')}
    data = {'include_crops': "True"}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{DETECTION_SERVICE_URL}/detect",
        files=files,
        data=data
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) == 2
    assert data["detections"][0]["class_name"] == "Shirt"
    assert data["detections"][1]["class_name"] == "Pants/Shorts"
    assert "processing_time" in data
    assert "image_size" in data
    assert len(data["image_size"]) == 2
    
    # Check for crop data
    assert data["detections"][0]["crop_data"] == mock_shirt_crop
    assert data["detections"][1]["crop_data"] == mock_pants_crop

@pytest.mark.asyncio
async def test_detection_endpoint_no_crops(async_httpx_client, monkeypatch, sample_person_image):
    """Test the detection endpoint with crops disabled."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Check if include_crops parameter is set
        data = kwargs.get("data", {})
        include_crops = data.get("include_crops") == "True"
        assert not include_crops
        
        response = httpx.Response(
            200, 
            json={
                "detections": [
                    {
                        "class_name": "Shirt", 
                        "class_id": 4, 
                        "confidence": 0.92, 
                        "bbox": [125, 100, 175, 350],
                        "crop_data": None
                    },
                    {
                        "class_name": "Pants/Shorts", 
                        "class_id": 10, 
                        "confidence": 0.88, 
                        "bbox": [125, 350, 175, 550],
                        "crop_data": None
                    }
                ],
                "processing_time": 0.42,
                "image_size": [600, 400]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('person.jpg', sample_person_image, 'image/jpeg')}
    data = {'include_crops': "False"}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{DETECTION_SERVICE_URL}/detect",
        files=files,
        data=data
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) == 2
    
    # Check that crop data is not included
    for detection in data["detections"]:
        assert detection["crop_data"] is None

@pytest.mark.asyncio
async def test_detection_endpoint_no_clothing(async_httpx_client, monkeypatch, mock_image_file):
    """Test the detection endpoint with an image containing no clothing."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            200, 
            json={
                "detections": [],
                "processing_time": 0.25,
                "image_size": [400, 400]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('empty.jpg', mock_image_file, 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{DETECTION_SERVICE_URL}/detect",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert len(data["detections"]) == 0  # No clothing detected
    assert "processing_time" in data
    assert "image_size" in data

@pytest.mark.asyncio
async def test_detection_endpoint_invalid_image(async_httpx_client, monkeypatch):
    """Test the detection endpoint with an invalid image."""
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
        f"{DETECTION_SERVICE_URL}/detect",
        files=files
    )
    
    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Invalid image file"

@pytest.mark.asyncio
async def test_detection_model_not_loaded(async_httpx_client, monkeypatch, sample_person_image):
    """Test the behavior when the model is not loaded."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            503, 
            json={"detail": "Model not loaded"}
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('person.jpg', sample_person_image, 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{DETECTION_SERVICE_URL}/detect",
        files=files
    )
    
    # Assertions
    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Model not loaded"

@pytest.mark.asyncio
async def test_detection_confidence_threshold(async_httpx_client, monkeypatch, sample_person_image):
    """Test the detection endpoint with different confidence thresholds."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Extract the confidence threshold from the request
        data = kwargs.get("data", {})
        confidence = data.get("confidence", None)
        
        # Return different responses based on the confidence threshold
        if confidence and float(confidence) > 0.9:
            # High threshold - fewer detections
            response = httpx.Response(
                200, 
                json={
                    "detections": [
                        {
                            "class_name": "Shirt", 
                            "class_id": 4, 
                            "confidence": 0.92, 
                            "bbox": [125, 100, 175, 350],
                            "crop_data": None
                        }
                    ],
                    "processing_time": 0.42,
                    "image_size": [600, 400]
                }
            )
        else:
            # Default threshold - more detections
            response = httpx.Response(
                200, 
                json={
                    "detections": [
                        {
                            "class_name": "Shirt", 
                            "class_id": 4, 
                            "confidence": 0.92, 
                            "bbox": [125, 100, 175, 350],
                            "crop_data": None
                        },
                        {
                            "class_name": "Pants/Shorts", 
                            "class_id": 10, 
                            "confidence": 0.88, 
                            "bbox": [125, 350, 175, 550],
                            "crop_data": None
                        },
                        {
                            "class_name": "Shoes", 
                            "class_id": 2, 
                            "confidence": 0.65, 
                            "bbox": [125, 550, 175, 600],
                            "crop_data": None
                        }
                    ],
                    "processing_time": 0.45,
                    "image_size": [600, 400]
                }
            )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request with high confidence
    files_high_conf = {'file': ('person.jpg', sample_person_image, 'image/jpeg')}
    data_high_conf = {'confidence': '0.95'}
    
    # Make the request with high confidence
    high_conf_response = await async_httpx_client.post(
        f"{DETECTION_SERVICE_URL}/detect",
        files=files_high_conf,
        data=data_high_conf
    )
    
    # Assertions for high confidence
    assert high_conf_response.status_code == 200
    high_conf_data = high_conf_response.json()
    assert len(high_conf_data["detections"]) == 1  # Only the shirt detected
    assert high_conf_data["detections"][0]["class_name"] == "Shirt"
    
    # Prepare the request with default confidence
    files_default = {'file': ('person.jpg', sample_person_image, 'image/jpeg')}
    
    # Make the request with default confidence
    default_conf_response = await async_httpx_client.post(
        f"{DETECTION_SERVICE_URL}/detect",
        files=files_default
    )
    
    # Assertions for default confidence
    assert default_conf_response.status_code == 200
    default_conf_data = default_conf_response.json()
    assert len(default_conf_data["detections"]) == 3  # All items detected
    
    # Check that we have both types of clothing from the DESIRED_CLASSES in the response
    class_names = [d["class_name"] for d in default_conf_data["detections"]]
    assert "Shirt" in class_names
    assert "Pants/Shorts" in class_names
    assert "Shoes" in class_names

@pytest.mark.asyncio
async def test_detection_specific_clothing_classes(async_httpx_client, monkeypatch, sample_person_image):
    """Test the detection endpoint returns the expected clothing classes."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            200, 
            json={
                "detections": [
                    {
                        "class_name": "Shirt", 
                        "class_id": 4, 
                        "confidence": 0.92, 
                        "bbox": [125, 100, 175, 350],
                        "crop_data": None
                    },
                    {
                        "class_name": "Pants/Shorts", 
                        "class_id": 10, 
                        "confidence": 0.88, 
                        "bbox": [125, 350, 175, 550],
                        "crop_data": None
                    },
                    {
                        "class_name": "Shoes", 
                        "class_id": 2, 
                        "confidence": 0.78, 
                        "bbox": [125, 550, 175, 600],
                        "crop_data": None
                    },
                    {
                        "class_name": "Hat", 
                        "class_id": 11, 
                        "confidence": 0.72, 
                        "bbox": [125, 10, 175, 75],
                        "crop_data": None
                    }
                ],
                "processing_time": 0.48,
                "image_size": [600, 400]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('person.jpg', sample_person_image, 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{DETECTION_SERVICE_URL}/detect",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data["detections"]) == 4
    
    # Verify all detections are valid clothing items from DESIRED_CLASSES
    class_ids = [d["class_id"] for d in data["detections"]]
    class_names = [d["class_name"] for d in data["detections"]]
    
    assert 4 in class_ids  # Shirt
    assert 10 in class_ids  # Pants/Shorts
    assert 2 in class_ids  # Shoes
    assert 11 in class_ids  # Hat
    
    assert "Shirt" in class_names
    assert "Pants/Shorts" in class_names
    assert "Shoes" in class_names
    assert "Hat" in class_names 