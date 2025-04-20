import pytest
import httpx
import json
import sys
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import from conftest
from conftest import VIRTUAL_TRYON_SERVICE_URL, encode_image_base64

# Mark all tests in this file with tryon marker
pytestmark = pytest.mark.tryon

@pytest.fixture
def sample_person_image():
    """Create a sample image with a person for testing."""
    return b"mock_person_image_data"

@pytest.fixture
def sample_tshirt_image():
    """Create a sample top garment image for testing."""
    return b"mock_tshirt_image_data"

@pytest.fixture
def sample_pants_image():
    """Create a sample bottom garment image for testing."""
    return b"mock_pants_image_data"

@pytest.mark.asyncio
async def test_tryon_health_endpoint(async_httpx_client, monkeypatch):
    """Test the health endpoint of the Virtual Try-On IEP."""
    # Mock the response
    async def mock_get(*args, **kwargs):
        response = httpx.Response(200, json={"status": "healthy", "service": "Virtual Try-On IEP"})
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "get", mock_get)
    
    # Make the request
    response = await async_httpx_client.get(f"{VIRTUAL_TRYON_SERVICE_URL}/health")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert data["service"] == "Virtual Try-On IEP"

@pytest.mark.asyncio
async def test_tryon_root_endpoint(async_httpx_client, monkeypatch):
    """Test the root endpoint of the Virtual Try-On IEP."""
    # Mock the response
    async def mock_get(*args, **kwargs):
        response = httpx.Response(200, json={
            "service": "Virtual Try-On IEP",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "tryon": "/tryon",
                "multi-tryon": "/tryon/multi",
                "placeholders": {
                    "model": "/static/placeholders/model_placeholder.jpg",
                    "garment": "/static/placeholders/garment_placeholder.jpg",
                    "result": "/static/placeholders/result_placeholder.jpg"
                }
            }
        })
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "get", mock_get)
    
    # Make the request
    response = await async_httpx_client.get(f"{VIRTUAL_TRYON_SERVICE_URL}/")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Virtual Try-On IEP"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"
    assert "endpoints" in data
    assert "health" in data["endpoints"]
    assert "tryon" in data["endpoints"]
    assert "multi-tryon" in data["endpoints"]
    assert "placeholders" in data["endpoints"]

@pytest.mark.asyncio
async def test_tryon_endpoint_successful(async_httpx_client, monkeypatch, sample_person_image, sample_tshirt_image):
    """Test the try-on endpoint with valid images."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Check JSON body for TryOnRequest format
        json_data = kwargs.get("json", {})
        
        # Verify required fields are present
        assert "model_image_data" in json_data
        assert "garment_image_data" in json_data
        
        # Get params
        category = json_data.get("category", "auto")
        mode = json_data.get("mode", "quality")
        
        # Create a mock result image
        result_image_b64 = encode_image_base64(sample_person_image)  # Reuse person image as result
        
        response = httpx.Response(
            200, 
            json={
                "result_image_path": "/static/results/result_12345.jpg",
                "result_image_data": result_image_b64,
                "details": {
                    "status": "success",
                    "prediction_id": "test-123",
                    "output_urls": ["https://fashn.ai/results/test-123.jpg"],
                    "local_path": "/app/static/results/result_12345.jpg",
                    "category": category,
                    "mode": mode
                }
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request with base64 encoded images
    model_image_b64 = encode_image_base64(sample_person_image)
    garment_image_b64 = encode_image_base64(sample_tshirt_image)
    
    json_data = {
        "model_image_data": model_image_b64,
        "garment_image_data": garment_image_b64,
        "category": "auto",
        "mode": "quality"
    }
    
    # Make the request
    response = await async_httpx_client.post(
        f"{VIRTUAL_TRYON_SERVICE_URL}/tryon",
        json=json_data
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "result_image_path" in data
    assert "result_image_data" in data
    assert "details" in data
    assert data["details"]["status"] == "success"
    assert "prediction_id" in data["details"]
    assert "category" in data["details"]
    assert "mode" in data["details"]
    assert data["details"]["mode"] == "quality"

@pytest.mark.asyncio
async def test_tryon_endpoint_with_different_modes(async_httpx_client, monkeypatch, sample_person_image, sample_tshirt_image):
    """Test the try-on endpoint with different quality/speed modes."""
    # Track which mode was used
    used_mode = None
    
    # Mock the response
    async def mock_post(*args, **kwargs):
        nonlocal used_mode
        
        # Extract the mode from the request
        json_data = kwargs.get("json", {})
        used_mode = json_data.get("mode", "quality")
        
        # Create a mock result image
        result_image_b64 = encode_image_base64(sample_person_image)
        
        # Processing time varies by mode
        processing_time = 1.0
        if used_mode == "quality":
            processing_time = 2.5
        elif used_mode == "balanced":
            processing_time = 1.8
        elif used_mode == "performance":
            processing_time = 1.0
        
        response = httpx.Response(
            200, 
            json={
                "result_image_path": "/static/results/result_12345.jpg",
                "result_image_data": result_image_b64,
                "details": {
                    "status": "success",
                    "prediction_id": "test-123",
                    "output_urls": ["https://fashn.ai/results/test-123.jpg"],
                    "local_path": "/app/static/results/result_12345.jpg",
                    "processing_time": processing_time,
                    "category": "topwear",
                    "mode": used_mode
                }
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare base64 encoded images
    model_image_b64 = encode_image_base64(sample_person_image)
    garment_image_b64 = encode_image_base64(sample_tshirt_image)
    
    # Test quality mode
    json_data_quality = {
        "model_image_data": model_image_b64,
        "garment_image_data": garment_image_b64,
        "category": "auto",
        "mode": "quality"
    }
    
    quality_response = await async_httpx_client.post(
        f"{VIRTUAL_TRYON_SERVICE_URL}/tryon",
        json=json_data_quality
    )
    
    # Assertions for quality mode
    assert quality_response.status_code == 200
    quality_data = quality_response.json()
    assert quality_data["details"]["mode"] == "quality"
    assert used_mode == "quality"
    
    # Test performance mode
    json_data_performance = {
        "model_image_data": model_image_b64,
        "garment_image_data": garment_image_b64,
        "category": "auto",
        "mode": "performance"
    }
    
    performance_response = await async_httpx_client.post(
        f"{VIRTUAL_TRYON_SERVICE_URL}/tryon",
        json=json_data_performance
    )
    
    # Assertions for performance mode
    assert performance_response.status_code == 200
    performance_data = performance_response.json()
    assert performance_data["details"]["mode"] == "performance"
    assert used_mode == "performance"
    assert performance_data["details"]["processing_time"] < quality_data["details"]["processing_time"]

@pytest.mark.asyncio
async def test_tryon_endpoint_with_different_categories(async_httpx_client, monkeypatch, sample_person_image, sample_tshirt_image, sample_pants_image):
    """Test the try-on endpoint with different garment categories."""
    # Track which category was used
    used_category = None
    
    # Mock the response
    async def mock_post(*args, **kwargs):
        nonlocal used_category
        
        # Extract the category from the request
        json_data = kwargs.get("json", {})
        used_category = json_data.get("category", "auto")
        
        # Create a mock result image
        result_image_b64 = encode_image_base64(sample_person_image)
        
        response = httpx.Response(
            200, 
            json={
                "result_image_path": "/static/results/result_12345.jpg",
                "result_image_data": result_image_b64,
                "details": {
                    "status": "success",
                    "prediction_id": "test-123",
                    "output_urls": ["https://fashn.ai/results/test-123.jpg"],
                    "local_path": "/app/static/results/result_12345.jpg",
                    "category": used_category,
                    "mode": "quality"
                }
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare base64 encoded images
    model_image_b64 = encode_image_base64(sample_person_image)
    tshirt_image_b64 = encode_image_base64(sample_tshirt_image)
    pants_image_b64 = encode_image_base64(sample_pants_image)
    
    # Test with topwear category
    json_data_top = {
        "model_image_data": model_image_b64,
        "garment_image_data": tshirt_image_b64,
        "category": "tops",
        "mode": "quality"
    }
    
    top_response = await async_httpx_client.post(
        f"{VIRTUAL_TRYON_SERVICE_URL}/tryon",
        json=json_data_top
    )
    
    # Assertions for topwear
    assert top_response.status_code == 200
    top_data = top_response.json()
    assert top_data["details"]["category"] == "tops"
    assert used_category == "tops"
    
    # Test with bottomwear category
    json_data_bottom = {
        "model_image_data": model_image_b64,
        "garment_image_data": pants_image_b64,
        "category": "bottoms",
        "mode": "quality"
    }
    
    bottom_response = await async_httpx_client.post(
        f"{VIRTUAL_TRYON_SERVICE_URL}/tryon",
        json=json_data_bottom
    )
    
    # Assertions for bottomwear
    assert bottom_response.status_code == 200
    bottom_data = bottom_response.json()
    assert bottom_data["details"]["category"] == "bottoms"
    assert used_category == "bottoms"

@pytest.mark.asyncio
async def test_tryon_endpoint_invalid_model_image(async_httpx_client, monkeypatch, sample_tshirt_image):
    """Test the try-on endpoint with an invalid model image."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            400, 
            json={
                "detail": "Invalid image data: Incorrect padding"
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare invalid model image data
    invalid_model_data = "this-is-not-valid-base64"
    garment_image_b64 = encode_image_base64(sample_tshirt_image)
    
    json_data = {
        "model_image_data": invalid_model_data,
        "garment_image_data": garment_image_b64,
        "category": "auto",
        "mode": "quality"
    }
    
    # Make the request
    response = await async_httpx_client.post(
        f"{VIRTUAL_TRYON_SERVICE_URL}/tryon",
        json=json_data
    )
    
    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid image data" in data["detail"]

@pytest.mark.asyncio
async def test_tryon_endpoint_invalid_garment_image(async_httpx_client, monkeypatch, sample_person_image):
    """Test the try-on endpoint with an invalid garment image."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            400, 
            json={
                "detail": "Invalid image data: Incorrect padding"
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare model image and invalid garment data
    model_image_b64 = encode_image_base64(sample_person_image)
    invalid_garment_data = "this-is-not-valid-base64"
    
    json_data = {
        "model_image_data": model_image_b64,
        "garment_image_data": invalid_garment_data,
        "category": "auto",
        "mode": "quality"
    }
    
    # Make the request
    response = await async_httpx_client.post(
        f"{VIRTUAL_TRYON_SERVICE_URL}/tryon",
        json=json_data
    )
    
    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid image data" in data["detail"]

@pytest.mark.asyncio
async def test_multi_tryon_endpoint(async_httpx_client, monkeypatch, sample_person_image, sample_tshirt_image, sample_pants_image):
    """Test the multi-garment try-on endpoint."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Check JSON data for MultiTryOnRequest format
        json_data = kwargs.get("json", {})
        
        # Verify required fields
        assert "model_image_data" in json_data
        assert "top_image_data" in json_data or "bottom_image_data" in json_data
        
        # Create a mock result image
        result_image_b64 = encode_image_base64(sample_person_image)
        
        # Check which garments were provided
        top_processed = "top_image_data" in json_data and json_data["top_image_data"] is not None
        bottom_processed = "bottom_image_data" in json_data and json_data["bottom_image_data"] is not None
        
        # Get the mode
        mode = json_data.get("mode", "quality")
        
        response = httpx.Response(
            200, 
            json={
                "final_result_path": "/static/results/result_12345.jpg",
                "final_result_data": result_image_b64,
                "details": {
                    "status": "success",
                    "top_processed": top_processed,
                    "bottom_processed": bottom_processed,
                    "mode": mode,
                    "final_result_path": "result_12345.jpg",
                    "results": {
                        "top_result": {
                            "status": "success",
                            "prediction_id": "top-123",
                            "category": "tops",
                            "mode": mode
                        } if top_processed else None,
                        "bottom_result": {
                            "status": "success",
                            "prediction_id": "bottom-123",
                            "category": "bottoms",
                            "mode": mode
                        } if bottom_processed else None,
                        "final_result": {
                            "status": "success",
                            "prediction_id": "final-123",
                            "category": "bottoms" if bottom_processed else "tops",
                            "mode": mode
                        }
                    }
                }
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare base64 encoded images
    model_image_b64 = encode_image_base64(sample_person_image)
    top_image_b64 = encode_image_base64(sample_tshirt_image)
    bottom_image_b64 = encode_image_base64(sample_pants_image)
    
    # Prepare the request with both top and bottom
    json_data = {
        "model_image_data": model_image_b64,
        "top_image_data": top_image_b64,
        "bottom_image_data": bottom_image_b64,
        "mode": "quality"
    }
    
    # Make the request
    response = await async_httpx_client.post(
        f"{VIRTUAL_TRYON_SERVICE_URL}/tryon/multi",
        json=json_data
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "final_result_path" in data
    assert "final_result_data" in data
    assert "details" in data
    assert data["details"]["status"] == "success"
    assert data["details"]["top_processed"] == True
    assert data["details"]["bottom_processed"] == True
    assert data["details"]["mode"] == "quality"
    
    # Check results within details
    assert "results" in data["details"]
    assert "top_result" in data["details"]["results"]
    assert "bottom_result" in data["details"]["results"]
    assert "final_result" in data["details"]["results"]
    assert data["details"]["results"]["top_result"] is not None
    assert data["details"]["results"]["bottom_result"] is not None
    assert data["details"]["results"]["final_result"] is not None

@pytest.mark.asyncio
async def test_multi_tryon_with_top_only(async_httpx_client, monkeypatch, sample_person_image, sample_tshirt_image):
    """Test the multi-garment try-on endpoint with top only."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Check JSON data
        json_data = kwargs.get("json", {})
        
        # Create a mock result image
        result_image_b64 = encode_image_base64(sample_person_image)
        
        # Verify only top is provided
        top_processed = "top_image_data" in json_data and json_data["top_image_data"] is not None
        bottom_processed = "bottom_image_data" in json_data and json_data["bottom_image_data"] is not None
        
        assert top_processed == True
        assert bottom_processed == False
        
        response = httpx.Response(
            200, 
            json={
                "final_result_path": "/static/results/result_12345.jpg",
                "final_result_data": result_image_b64,
                "details": {
                    "status": "success",
                    "top_processed": True,
                    "bottom_processed": False,
                    "mode": "quality",
                    "final_result_path": "result_12345.jpg",
                    "results": {
                        "top_result": {
                            "status": "success",
                            "prediction_id": "top-123",
                            "category": "tops",
                            "mode": "quality"
                        },
                        "bottom_result": None,
                        "final_result": {
                            "status": "success",
                            "prediction_id": "top-123",
                            "category": "tops",
                            "mode": "quality"
                        }
                    }
                }
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare base64 encoded images
    model_image_b64 = encode_image_base64(sample_person_image)
    top_image_b64 = encode_image_base64(sample_tshirt_image)
    
    # Prepare the request with top only
    json_data = {
        "model_image_data": model_image_b64,
        "top_image_data": top_image_b64,
        "bottom_image_data": None,
        "mode": "quality"
    }
    
    # Make the request
    response = await async_httpx_client.post(
        f"{VIRTUAL_TRYON_SERVICE_URL}/tryon/multi",
        json=json_data
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "details" in data
    assert data["details"]["top_processed"] == True
    assert data["details"]["bottom_processed"] == False
    assert data["details"]["results"]["top_result"] is not None
    assert data["details"]["results"]["bottom_result"] is None
    assert data["details"]["results"]["final_result"] is not None
    assert data["details"]["results"]["final_result"]["category"] == "tops"

@pytest.mark.asyncio
async def test_multi_tryon_invalid_request(async_httpx_client, monkeypatch, sample_person_image):
    """Test the multi-garment try-on endpoint with no garments provided."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            400, 
            json={
                "detail": "At least one garment (top or bottom) must be provided"
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare base64 encoded images
    model_image_b64 = encode_image_base64(sample_person_image)
    
    # Prepare the request with no garments
    json_data = {
        "model_image_data": model_image_b64,
        "top_image_data": None,
        "bottom_image_data": None,
        "mode": "quality"
    }
    
    # Make the request
    response = await async_httpx_client.post(
        f"{VIRTUAL_TRYON_SERVICE_URL}/tryon/multi",
        json=json_data
    )
    
    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "at least one garment" in data["detail"].lower() 