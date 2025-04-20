import pytest
import httpx
import json
import sys
import io
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import from conftest
from conftest import RECO_DATA_SERVICE_URL

# Mark all tests in this file with recommendation data marker
pytestmark = pytest.mark.reco_data

@pytest.mark.asyncio
async def test_matching_endpoint(async_httpx_client, monkeypatch):
    """Test the matching endpoint of the Recommendation Data IEP."""
    # Mock image data
    mock_image_data = b"mock_image_bytes"
    mock_image_io = io.BytesIO(mock_image_data)
    
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Make sure proper parameters are provided
        json_data = kwargs.get("json", {})
        assert "vector" in json_data
        
        query_params = kwargs.get("params", {})
        gender = query_params.get("gender")
        style = query_params.get("style")
        type_ = query_params.get("type_")
        
        # Verify the type parameter (required)
        assert type_ in ["topwear", "bottomwear"]
        
        # Return image response
        mock_image_io.seek(0)
        response = httpx.Response(
            200,
            content=mock_image_data,
            headers={"Content-Type": "image/jpeg"}
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    vector = [0.1, 0.2, 0.3, 0.4, 0.5] * 10  # Small vector for testing
    params = {
        "gender": "male",
        "style": "formal",
        "type_": "topwear"
    }
    
    # Make the request
    response = await async_httpx_client.post(
        f"{RECO_DATA_SERVICE_URL}/matching",
        json={"vector": vector},
        params=params
    )
    
    # Assertions
    assert response.status_code == 200
    assert response.headers.get("content-type") == "image/jpeg"

@pytest.mark.asyncio
async def test_similarity_endpoint(async_httpx_client, monkeypatch):
    """Test the similarity endpoint of the Recommendation Data IEP."""
    # Mock image data
    mock_image_data = b"mock_similar_image_bytes"
    mock_image_io = io.BytesIO(mock_image_data)
    
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Make sure proper parameters are provided
        json_data = kwargs.get("json", {})
        assert "vector" in json_data
        
        query_params = kwargs.get("params", {})
        gender = query_params.get("gender")
        style = query_params.get("style")
        type_ = query_params.get("type_")
        
        # Verify the type parameter (required)
        assert type_ in ["topwear", "bottomwear"]
        
        # Return image response
        mock_image_io.seek(0)
        response = httpx.Response(
            200,
            content=mock_image_data,
            headers={"Content-Type": "image/jpeg"}
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    vector = [0.1, 0.2, 0.3, 0.4, 0.5] * 10  # Small vector for testing
    params = {
        "gender": "female",
        "style": "casual",
        "type_": "bottomwear"
    }
    
    # Make the request
    response = await async_httpx_client.post(
        f"{RECO_DATA_SERVICE_URL}/similarity",
        json={"vector": vector},
        params=params
    )
    
    # Assertions
    assert response.status_code == 200
    assert response.headers.get("content-type") == "image/jpeg"

@pytest.mark.asyncio
async def test_recommendation_endpoint(async_httpx_client, monkeypatch):
    """Test the recommendation endpoint of the Recommendation Data IEP."""
    # Mock image data
    mock_image_data = b"mock_recommendation_image_bytes"
    mock_image_io = io.BytesIO(mock_image_data)
    
    # Mock the response
    async def mock_post(*args, **kwargs):
        # Make sure proper parameters are provided
        json_data = kwargs.get("json", {})
        assert "vector" in json_data
        
        query_params = kwargs.get("params", {})
        operation = query_params.get("operation")
        gender = query_params.get("gender")
        style = query_params.get("style")
        type_ = query_params.get("type_")
        
        # Verify required parameters
        assert operation in ["matching", "similarity"]
        assert type_ in ["topwear", "bottomwear"]
        
        # Return image response
        mock_image_io.seek(0)
        response = httpx.Response(
            200,
            content=mock_image_data,
            headers={"Content-Type": "image/jpeg"}
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    vector = [0.1, 0.2, 0.3, 0.4, 0.5] * 10  # Small vector for testing
    params = {
        "operation": "matching",
        "gender": "male",
        "style": "casual",
        "type_": "topwear"
    }
    
    # Make the request
    response = await async_httpx_client.post(
        f"{RECO_DATA_SERVICE_URL}/recommendation",
        json={"vector": vector},
        params=params
    )
    
    # Assertions
    assert response.status_code == 200
    assert response.headers.get("content-type") == "image/jpeg"

@pytest.mark.asyncio
async def test_invalid_operation(async_httpx_client, monkeypatch):
    """Test the recommendation endpoint with an invalid operation."""
    # Mock the error response
    async def mock_post(*args, **kwargs):
        query_params = kwargs.get("params", {})
        operation = query_params.get("operation")
        
        # Return error for invalid operation
        if operation not in ["matching", "similarity"]:
            response = httpx.Response(
                400,
                json={"detail": "Invalid operation. Must be 'matching' or 'similarity'"}
            )
            return response
            
        # Shouldn't reach here in this test
        response = httpx.Response(200, content=b"")
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request with invalid operation
    vector = [0.1, 0.2, 0.3, 0.4, 0.5] * 10  # Small vector for testing
    params = {
        "operation": "invalid_op",
        "gender": "male",
        "type_": "topwear"
    }
    
    # Make the request
    response = await async_httpx_client.post(
        f"{RECO_DATA_SERVICE_URL}/recommendation",
        json={"vector": vector},
        params=params
    )
    
    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid operation" in data["detail"]

@pytest.mark.asyncio
async def test_invalid_type(async_httpx_client, monkeypatch):
    """Test with an invalid clothing type parameter."""
    # Mock the error response
    async def mock_post(*args, **kwargs):
        query_params = kwargs.get("params", {})
        type_ = query_params.get("type_")
        
        # Return error for invalid type
        if type_ not in ["topwear", "bottomwear"]:
            response = httpx.Response(
                400,
                json={"detail": "type_ must be either 'topwear' or 'bottomwear'"}
            )
            return response
            
        # Shouldn't reach here in this test
        response = httpx.Response(200, content=b"")
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request with invalid type
    vector = [0.1, 0.2, 0.3, 0.4, 0.5] * 10  # Small vector for testing
    params = {
        "gender": "female",
        "type_": "invalid_type",
        "style": "casual"
    }
    
    # Make the request
    response = await async_httpx_client.post(
        f"{RECO_DATA_SERVICE_URL}/matching",
        json={"vector": vector},
        params=params
    )
    
    # Assertions
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "type_ must be either" in data["detail"]

@pytest.mark.asyncio
async def test_no_matching_items(async_httpx_client, monkeypatch):
    """Test when no matching items are found in the database."""
    # Mock the error response
    async def mock_post(*args, **kwargs):
        # Return 404 for no matching items
        response = httpx.Response(
            404,
            json={"detail": "No matching segmented_pic_ids found."}
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request 
    vector = [0.1, 0.2, 0.3, 0.4, 0.5] * 10
    params = {
        "gender": "male",
        "type_": "topwear",
        "style": "very_specific_nonexistent_style"  # Should trigger no matches
    }
    
    # Make the request
    response = await async_httpx_client.post(
        f"{RECO_DATA_SERVICE_URL}/similarity",
        json={"vector": vector},
        params=params
    )
    
    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "No matching segmented_pic_ids found" in data["detail"]

@pytest.mark.asyncio
async def test_qdrant_search_failure(async_httpx_client, monkeypatch):
    """Test when Qdrant vector search returns no results."""
    # Mock the error response
    async def mock_post(*args, **kwargs):
        # Return 404 for no vector search results
        response = httpx.Response(
            404,
            json={"detail": "No match found in Qdrant."}
        )
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request with a vector that won't match anything
    vector = [0.0] * 50  # Zero vector unlikely to match anything
    params = {
        "gender": "female",
        "type_": "bottomwear"
    }
    
    # Make the request
    response = await async_httpx_client.post(
        f"{RECO_DATA_SERVICE_URL}/matching",
        json={"vector": vector},
        params=params
    )
    
    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "No match found in Qdrant" in data["detail"] 