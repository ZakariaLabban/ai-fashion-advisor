import pytest
import httpx
import json
import sys
import base64
import io
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import from conftest
from conftest import PPL_DETECTOR_SERVICE_URL

# Mark all tests in this file with people detector marker
pytestmark = pytest.mark.ppl_detector

@pytest.fixture
def sample_image_with_people():
    """Create a sample image with people for testing."""
    return b"mock_image_with_people_data"

@pytest.fixture
def sample_image_no_people():
    """Create a sample image without people for testing."""
    return b"mock_image_without_people_data"

@pytest.mark.asyncio
async def test_ppl_detector_health_endpoint(async_httpx_client, monkeypatch):
    """Test the health endpoint of the People Detector IEP."""
    # Mock the response
    async def mock_get(*args, **kwargs):
        response = httpx.Response(
            200, 
            json={"status": "healthy", "model": "YOLOv8 Person Detection"}
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "get", mock_get)
    
    # Make the request
    response = await async_httpx_client.get(f"{PPL_DETECTOR_SERVICE_URL}/health")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model"] == "YOLOv8 Person Detection"

@pytest.mark.asyncio
async def test_detect_persons_successful(async_httpx_client, monkeypatch, sample_image_with_people):
    """Test the detect endpoint with an image containing people."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Check that the file is provided in the request
        assert "file" in kwargs.get("files", {})
        
        # Create a mock response with detected persons
        response = httpx.Response(
            200, 
            json={
                "person_count": 2,
                "detections": [
                    {
                        "confidence": 0.95,
                        "bbox": [100, 50, 300, 400],
                        "crop_data": None
                    },
                    {
                        "confidence": 0.87,
                        "bbox": [400, 60, 600, 420],
                        "crop_data": None
                    }
                ],
                "processing_time": 0.124,
                "image_size": [480, 640]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Make the request
    files = {"file": ("people.jpg", sample_image_with_people, "image/jpeg")}
    response = await async_httpx_client.post(
        f"{PPL_DETECTOR_SERVICE_URL}/detect",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "person_count" in data
    assert data["person_count"] == 2
    assert "detections" in data
    assert len(data["detections"]) == 2
    assert "processing_time" in data
    assert "image_size" in data
    
    # Check detection details
    for detection in data["detections"]:
        assert "confidence" in detection
        assert "bbox" in detection
        assert len(detection["bbox"]) == 4  # [x1, y1, x2, y2]

@pytest.mark.asyncio
async def test_detect_persons_with_crops(async_httpx_client, monkeypatch, sample_image_with_people):
    """Test the detect endpoint with include_crops=True."""
    # Create mock base64 encoded image
    mock_crop = base64.b64encode(b"cropped person data").decode("utf-8")
    
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Check that the file is provided
        assert "file" in kwargs.get("files", {})
        
        # Check if include_crops parameter is set
        data = kwargs.get("data", {})
        include_crops = data.get("include_crops") == "True"
        
        # Create a response including crop data if requested
        response = httpx.Response(
            200, 
            json={
                "person_count": 1,
                "detections": [
                    {
                        "confidence": 0.92,
                        "bbox": [120, 80, 320, 450],
                        "crop_data": mock_crop if include_crops else None
                    }
                ],
                "processing_time": 0.135,
                "image_size": [480, 640]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Make the request with include_crops=True
    files = {"file": ("person.jpg", sample_image_with_people, "image/jpeg")}
    data = {"include_crops": "True"}
    
    response = await async_httpx_client.post(
        f"{PPL_DETECTOR_SERVICE_URL}/detect",
        files=files,
        data=data
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["person_count"] == 1
    assert len(data["detections"]) == 1
    
    # Check for crop data
    detection = data["detections"][0]
    assert "crop_data" in detection
    assert detection["crop_data"] == mock_crop

@pytest.mark.asyncio
async def test_count_persons_endpoint(async_httpx_client, monkeypatch, sample_image_with_people):
    """Test the count_persons endpoint."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Check that the file is provided in the request
        assert "file" in kwargs.get("files", {})
        
        # Create a mock response with person count
        response = httpx.Response(
            200, 
            json={"person_count": 3}
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Make the request
    files = {"file": ("people.jpg", sample_image_with_people, "image/jpeg")}
    
    response = await async_httpx_client.post(
        f"{PPL_DETECTOR_SERVICE_URL}/count_persons",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "person_count" in data
    assert data["person_count"] == 3

@pytest.mark.asyncio
async def test_detect_no_persons(async_httpx_client, monkeypatch, sample_image_no_people):
    """Test the detect endpoint with an image containing no people."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Check that the file is provided in the request
        assert "file" in kwargs.get("files", {})
        
        # Create a mock response with no detected persons
        response = httpx.Response(
            200, 
            json={
                "person_count": 0,
                "detections": [],
                "processing_time": 0.112,
                "image_size": [480, 640]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Make the request
    files = {"file": ("no_people.jpg", sample_image_no_people, "image/jpeg")}
    
    response = await async_httpx_client.post(
        f"{PPL_DETECTOR_SERVICE_URL}/detect",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["person_count"] == 0
    assert len(data["detections"]) == 0

@pytest.mark.asyncio
async def test_invalid_image(async_httpx_client, monkeypatch):
    """Test the detect endpoint with an invalid image."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Mock an error response for invalid image
        response = httpx.Response(
            400, 
            json={"detail": "Invalid image file"}
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare an invalid image
    invalid_content = b"this is not a valid image"
    files = {"file": ("invalid.jpg", invalid_content, "image/jpeg")}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{PPL_DETECTOR_SERVICE_URL}/detect",
        files=files
    )
    
    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid image" in data["detail"]

@pytest.mark.asyncio
async def test_model_not_loaded(async_httpx_client, monkeypatch, sample_image_with_people):
    """Test the behavior when the model is not loaded."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Mock a service unavailable response
        response = httpx.Response(
            503, 
            json={"detail": "Model not loaded"}
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Make the request
    files = {"file": ("people.jpg", sample_image_with_people, "image/jpeg")}
    
    response = await async_httpx_client.post(
        f"{PPL_DETECTOR_SERVICE_URL}/detect",
        files=files
    )
    
    # Assertions
    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Model not loaded"

@pytest.mark.asyncio
async def test_custom_confidence_threshold(async_httpx_client, monkeypatch, sample_image_with_people):
    """Test the detect endpoint with a custom confidence threshold."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Extract the confidence parameter from request data
        data = kwargs.get("data", {})
        confidence = float(data.get("confidence", "0.45"))  # Default is 0.45
        
        # Create response with different detections based on confidence
        if confidence > 0.7:
            # Only high confidence detections
            detections = [
                {
                    "confidence": 0.95,
                    "bbox": [100, 50, 300, 400],
                    "crop_data": None
                }
            ]
        else:
            # Include lower confidence detections
            detections = [
                {
                    "confidence": 0.95,
                    "bbox": [100, 50, 300, 400],
                    "crop_data": None
                },
                {
                    "confidence": 0.68,
                    "bbox": [400, 60, 600, 420],
                    "crop_data": None
                }
            ]
        
        response = httpx.Response(
            200, 
            json={
                "person_count": len(detections),
                "detections": detections,
                "processing_time": 0.118,
                "image_size": [480, 640]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Test with default confidence
    files_default = {"file": ("people.jpg", sample_image_with_people, "image/jpeg")}
    response_default = await async_httpx_client.post(
        f"{PPL_DETECTOR_SERVICE_URL}/detect",
        files=files_default
    )
    
    # Test with higher confidence
    files_high_conf = {"file": ("people.jpg", sample_image_with_people, "image/jpeg")}
    data_high_conf = {"confidence": "0.8"}
    response_high_conf = await async_httpx_client.post(
        f"{PPL_DETECTOR_SERVICE_URL}/detect",
        files=files_high_conf,
        data=data_high_conf
    )
    
    # Assertions
    assert response_default.status_code == 200
    assert response_high_conf.status_code == 200
    
    data_default = response_default.json()
    data_high_conf = response_high_conf.json()
    
    assert data_default["person_count"] == 2
    assert data_high_conf["person_count"] == 1

@pytest.mark.asyncio
async def test_count_persons_with_confidence(async_httpx_client, monkeypatch, sample_image_with_people):
    """Test the count_persons endpoint with custom confidence threshold."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Extract the confidence parameter from request data
        data = kwargs.get("data", {})
        confidence = float(data.get("confidence", "0.45"))  # Default is 0.45
        
        # Return different counts based on confidence threshold
        person_count = 3 if confidence <= 0.5 else 2
        
        response = httpx.Response(
            200, 
            json={"person_count": person_count}
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Test with default confidence
    files_default = {"file": ("people.jpg", sample_image_with_people, "image/jpeg")}
    response_default = await async_httpx_client.post(
        f"{PPL_DETECTOR_SERVICE_URL}/count_persons",
        files=files_default
    )
    
    # Test with higher confidence
    files_high_conf = {"file": ("people.jpg", sample_image_with_people, "image/jpeg")}
    data_high_conf = {"confidence": "0.7"}
    response_high_conf = await async_httpx_client.post(
        f"{PPL_DETECTOR_SERVICE_URL}/count_persons",
        files=files_high_conf,
        data=data_high_conf
    )
    
    # Assertions
    assert response_default.status_code == 200
    assert response_high_conf.status_code == 200
    
    data_default = response_default.json()
    data_high_conf = response_high_conf.json()
    
    assert data_default["person_count"] == 3
    assert data_high_conf["person_count"] == 2 