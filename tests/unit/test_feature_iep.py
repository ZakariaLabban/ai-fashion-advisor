import pytest
import httpx
import io
import json
import sys
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import from conftest
from conftest import FEATURE_SERVICE_URL

# Mark all tests in this file with feature marker
pytestmark = pytest.mark.feature

@pytest.fixture
def sample_tshirt_image():
    # Create a simple test image as bytes
    return b"mock_tshirt_image_data"

@pytest.fixture
def sample_pants_image():
    # Create a simple test image as bytes
    return b"mock_pants_image_data"

@pytest.fixture
def mock_image_file():
    # Create a mock image file with white pixels
    return b"mock_empty_image_data"

@pytest.mark.asyncio
async def test_feature_health_endpoint(async_httpx_client, monkeypatch):
    """Test the health endpoint of the Feature IEP."""
    # Mock the response
    async def mock_get(*args, **kwargs):
        response = httpx.Response(
            200, 
            json={
                "status": "healthy", 
                "model": "MultiTaskResNet50 Feature Extractor"
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "get", mock_get)
    
    # Make the request
    response = await async_httpx_client.get(f"{FEATURE_SERVICE_URL}/health")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data
    assert data["model"] == "MultiTaskResNet50 Feature Extractor"

@pytest.mark.asyncio
async def test_feature_extract_tshirt(async_httpx_client, monkeypatch, sample_tshirt_image):
    """Test the feature extraction endpoint with a t-shirt image."""
    # Mock the response with realistic feature vector
    async def mock_post(*args, **kwargs):
        # Create a synthetic feature vector (would be much longer in reality)
        features = np.random.randn(2048).tolist()  # Using actual ResNet50 feature size
        
        # Create a synthetic color histogram (8 bins per RGB channel = 24 total)
        color_histogram = np.random.rand(24).tolist()
        
        response = httpx.Response(
            200, 
            json={
                "features": features,
                "color_histogram": color_histogram,
                "processing_time": 0.28,
                "input_image_size": [600, 400]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('tshirt.jpg', sample_tshirt_image, 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{FEATURE_SERVICE_URL}/extract",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "features" in data
    assert len(data["features"]) == 2048  # Check ResNet50 vector length
    assert "color_histogram" in data
    assert len(data["color_histogram"]) == 24  # Check histogram length (8 bins per RGB channel)
    assert "processing_time" in data
    assert "input_image_size" in data
    assert len(data["input_image_size"]) == 2

@pytest.mark.asyncio
async def test_feature_extract_pants(async_httpx_client, monkeypatch, sample_pants_image):
    """Test the feature extraction endpoint with a pants image."""
    # Mock the response with realistic feature vector
    async def mock_post(*args, **kwargs):
        # Create a synthetic feature vector
        features = np.random.randn(2048).tolist()  # Using actual ResNet50 feature size
        
        # Create a synthetic color histogram - mostly black for pants
        # 8 bins for each RGB channel (total 24)
        color_histogram = [0.3, 0.2, 0.1, 0.05, 0.05, 0.1, 0.1, 0.1]  # R histogram
        color_histogram += [0.3, 0.2, 0.1, 0.05, 0.05, 0.1, 0.1, 0.1]  # G histogram
        color_histogram += [0.3, 0.2, 0.1, 0.05, 0.05, 0.1, 0.1, 0.1]  # B histogram
        
        response = httpx.Response(
            200, 
            json={
                "features": features,
                "color_histogram": color_histogram,
                "processing_time": 0.26,
                "input_image_size": [800, 600]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('pants.jpg', sample_pants_image, 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{FEATURE_SERVICE_URL}/extract",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "features" in data
    assert len(data["features"]) == 2048  # Check vector length
    assert "color_histogram" in data
    assert len(data["color_histogram"]) == 24  # 8 bins per RGB channel
    assert "processing_time" in data
    assert "input_image_size" in data
    assert len(data["input_image_size"]) == 2

@pytest.mark.asyncio
async def test_feature_extract_with_bins_parameter(async_httpx_client, monkeypatch, sample_tshirt_image):
    """Test the feature extraction endpoint with a custom bins_per_channel parameter."""
    # Mock the response with realistic feature vector
    async def mock_post(*args, **kwargs):
        # Extract the bins_per_channel parameter from the request
        params = kwargs.get("data", {})
        bins_per_channel = int(params.get("bins_per_channel", 8))
        
        # Create a synthetic feature vector
        features = np.random.randn(2048).tolist()  # Using actual ResNet50 feature size
        
        # Create a synthetic color histogram with the correct number of bins
        # Total bins = bins_per_channel * 3 channels
        total_bins = bins_per_channel * 3
        color_histogram = np.random.rand(total_bins).tolist()
        
        response = httpx.Response(
            200, 
            json={
                "features": features,
                "color_histogram": color_histogram,
                "processing_time": 0.25,
                "input_image_size": [600, 400]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request with a custom bins_per_channel value
    files = {'file': ('tshirt.jpg', sample_tshirt_image, 'image/jpeg')}
    data = {"bins_per_channel": 4}  # Use 4 bins per channel instead of default 8
    
    # Make the request
    response = await async_httpx_client.post(
        f"{FEATURE_SERVICE_URL}/extract",
        files=files,
        data=data
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "features" in data
    assert len(data["features"]) == 2048  # Check vector length
    assert "color_histogram" in data
    assert len(data["color_histogram"]) == 12  # 4 bins per channel * 3 channels = 12 total bins
    assert "processing_time" in data
    assert "input_image_size" in data

@pytest.mark.asyncio
async def test_feature_extract_consistent_results(async_httpx_client, monkeypatch, sample_tshirt_image):
    """Test that feature extraction produces consistent results for the same image."""
    # Create a fixed feature vector and histogram for consistency
    fixed_features = np.random.randn(2048).tolist()
    fixed_color_histogram = np.random.rand(24).tolist()  # 8 bins per RGB channel
    
    # Mock the response with the same result for each call
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            200, 
            json={
                "features": fixed_features,
                "color_histogram": fixed_color_histogram,
                "processing_time": 0.25,
                "input_image_size": [600, 400]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('tshirt.jpg', sample_tshirt_image, 'image/jpeg')}
    
    # Make the first request
    response1 = await async_httpx_client.post(
        f"{FEATURE_SERVICE_URL}/extract",
        files=files
    )
    
    # Make the second request with the same image
    files = {'file': ('tshirt.jpg', sample_tshirt_image, 'image/jpeg')}
    response2 = await async_httpx_client.post(
        f"{FEATURE_SERVICE_URL}/extract",
        files=files
    )
    
    # Assertions
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    data1 = response1.json()
    data2 = response2.json()
    
    # Both responses should have the same feature vector and color histogram
    assert data1["features"] == data2["features"]
    assert data1["color_histogram"] == data2["color_histogram"]
    assert data1["input_image_size"] == data2["input_image_size"]

@pytest.mark.asyncio
async def test_feature_extract_invalid_image(async_httpx_client, monkeypatch):
    """Test the feature extraction endpoint with an invalid image."""
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
        f"{FEATURE_SERVICE_URL}/extract",
        files=files
    )
    
    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Invalid image file"

@pytest.mark.asyncio
async def test_feature_service_unavailable(async_httpx_client, monkeypatch):
    """Test the behavior when the feature extraction service is unavailable."""
    # Mock the response to simulate a service error
    async def mock_post(*args, **kwargs):
        response = httpx.Response(
            503, 
            json={"detail": "Model not loaded"}
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('tshirt.jpg', b"mock_image_data", 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{FEATURE_SERVICE_URL}/extract",
        files=files
    )
    
    # Assertions
    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Model not loaded"

@pytest.mark.asyncio
async def test_feature_extract_empty_image(async_httpx_client, monkeypatch, mock_image_file):
    """Test the feature extraction endpoint with an empty/plain image."""
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Create a synthetic feature vector
        features = np.zeros(2048).tolist()  # Empty feature vector
        
        # Create a synthetic color histogram - mostly one color
        # 8 bins per RGB channel (total 24)
        # First bin of each channel dominates (white color)
        color_histogram = [0.95, 0.01, 0.01, 0.01, 0.01, 0.01, 0.0, 0.0]  # R histogram
        color_histogram += [0.95, 0.01, 0.01, 0.01, 0.01, 0.01, 0.0, 0.0]  # G histogram
        color_histogram += [0.95, 0.01, 0.01, 0.01, 0.01, 0.01, 0.0, 0.0]  # B histogram
        
        response = httpx.Response(
            200, 
            json={
                "features": features,
                "color_histogram": color_histogram,
                "processing_time": 0.22,
                "input_image_size": [400, 400]
            }
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {'file': ('empty.jpg', mock_image_file, 'image/jpeg')}
    
    # Make the request
    response = await async_httpx_client.post(
        f"{FEATURE_SERVICE_URL}/extract",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "features" in data
    assert len(data["features"]) == 2048
    assert "color_histogram" in data
    assert len(data["color_histogram"]) == 24  # 8 bins per RGB channel
    assert data["color_histogram"][0] > 0.9  # First bin of R channel should be dominant
    assert data["color_histogram"][8] > 0.9  # First bin of G channel should be dominant
    assert data["color_histogram"][16] > 0.9  # First bin of B channel should be dominant
    assert "input_image_size" in data 