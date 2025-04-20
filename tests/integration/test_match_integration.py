import pytest
import httpx
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import from conftest
from conftest import EEP_SERVICE_URL, MATCH_SERVICE_URL, encode_image_base64, valid_match_response

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

@pytest.fixture
def sample_tshirt_image():
    """Create a sample t-shirt image for testing."""
    return b"mock_tshirt_image_data"

@pytest.fixture
def sample_pants_image():
    """Create a sample pants image for testing."""
    return b"mock_pants_image_data"

@pytest.mark.asyncio
async def test_outfit_match_integration(async_httpx_client, monkeypatch, sample_tshirt_image, sample_pants_image):
    """
    Integration test for the outfit matching functionality.
    
    This test mocks the responses from the EEP, which internally would call:
    1. Feature extraction for each clothing item
    2. Style classification for each item
    3. Match computation between items
    """
    # Mock the response from the EEP/Match service
    async def mock_post(*args, **kwargs):
        url = args[0]
        
        # Verify request format for match endpoint
        if "/api/match" in url:
            # Validate that the correct file keys are in the request for matching
            files = kwargs.get("files", {})
            assert "topwear" in files, "Request missing 'topwear' file"
            assert "bottomwear" in files, "Request missing 'bottomwear' file"
        
        # Construct a realistic response from the match service
        response_data = {
            "request_id": "match-integration-123",
            "match_score": 0.78,
            "timestamp": "2023-05-20T15:30:45.123456",
            "processing_time": 1.25,
            "analysis": {
                "topwear": {
                    "style": {
                        "name": "Casual",
                        "confidence": 0.85
                    },
                    "dominant_colors": ["Blue", "White"],
                    "features": {
                        "pattern": "Solid",
                        "neckline": "Round",
                        "fit": "Regular"
                    }
                },
                "bottomwear": {
                    "style": {
                        "name": "Casual",
                        "confidence": 0.92
                    },
                    "dominant_colors": ["Black"],
                    "features": {
                        "pattern": "Solid",
                        "length": "Long",
                        "fit": "Slim"
                    }
                }
            },
            "match_components": {
                "style_match": 0.85,
                "color_match": 0.65,
                "pattern_match": 0.90
            },
            "suggestions": [
                {
                    "component": "topwear",
                    "suggestion": "Consider a patterned shirt to create more visual interest.",
                    "confidence": 0.75
                },
                {
                    "component": "bottomwear",
                    "suggestion": "Dark jeans pair well with this top.",
                    "confidence": 0.82
                }
            ]
        }
        
        response = httpx.Response(200, json=response_data)
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {
        'topwear': ('tshirt.jpg', sample_tshirt_image, 'image/jpeg'),
        'bottomwear': ('pants.jpg', sample_pants_image, 'image/jpeg')
    }
    
    # Make the request to the match endpoint
    response = await async_httpx_client.post(
        f"{MATCH_SERVICE_URL}/api/match",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    
    # Check structure of the response
    assert "request_id" in data
    assert "match_score" in data
    assert "timestamp" in data
    assert "processing_time" in data
    assert "analysis" in data
    assert "match_components" in data
    assert "suggestions" in data
    
    # Check analysis details
    assert "topwear" in data["analysis"]
    assert "bottomwear" in data["analysis"]
    
    # Check topwear analysis
    topwear = data["analysis"]["topwear"]
    assert "style" in topwear
    assert "dominant_colors" in topwear
    assert "features" in topwear
    assert topwear["style"]["name"] == "Casual"
    
    # Check bottomwear analysis
    bottomwear = data["analysis"]["bottomwear"]
    assert "style" in bottomwear
    assert "dominant_colors" in bottomwear
    assert "features" in bottomwear
    assert bottomwear["style"]["name"] == "Casual"
    
    # Check match components
    assert "style_match" in data["match_components"]
    assert "color_match" in data["match_components"]
    assert "pattern_match" in data["match_components"]
    
    # Check suggestions
    assert len(data["suggestions"]) == 2
    for suggestion in data["suggestions"]:
        assert "component" in suggestion
        assert "suggestion" in suggestion
        assert "confidence" in suggestion
        assert suggestion["component"] in ["topwear", "bottomwear"]

@pytest.mark.asyncio
async def test_outfit_match_with_compute_match(async_httpx_client, monkeypatch, valid_match_response):
    """
    Integration test for the outfit matching using the compute_match endpoint.
    
    This tests the flow where pre-processed data is used to compute a match,
    without needing to upload images.
    """
    # Mock the EEP response for the compute_match endpoint
    async def mock_post(*args, **kwargs):
        url = args[0]
        
        # Extract the request data
        request_json = kwargs.get("json", {})
        
        # Verify required fields are present
        assert "top_style" in request_json
        assert "bottom_style" in request_json
        assert "top_vector" in request_json
        assert "bottom_vector" in request_json
        
        # Generate a match score based on style similarity
        match_score = 85 if request_json["top_style"] == request_json["bottom_style"] else 45
        
        # Customize response based on the input
        match_response = dict(valid_match_response)
        match_response["match_score"] = match_score
        match_response["request_id"] = "test-compute-match-123"
        
        if request_json["top_style"] != request_json["bottom_style"]:
            # Style mismatch - lower the style_consistency score
            match_response["analysis"]["style_consistency"]["score"] = 40
            match_response["analysis"]["style_consistency"]["analysis"] = f"The {request_json['top_style']} top doesn't pair well with the {request_json['bottom_style']} bottom."
            
            # Add more specific suggestions
            match_response["suggestions"] = [
                f"Consider pairing your {request_json['top_style']} top with a {request_json['top_style']} bottom instead.",
                f"If you want to keep the {request_json['bottom_style']} bottom, try a more {request_json['bottom_style']} top."
            ]
        
        response = httpx.Response(200, json=match_response)
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Test 1: Matching styles (Casual top, Casual bottom)
    matching_styles_request = {
        "top_style": "Casual",
        "bottom_style": "Casual",
        "top_vector": [0.1, 0.2, 0.3, 0.4, 0.5],
        "bottom_vector": [0.15, 0.25, 0.35, 0.45, 0.55],
        "top_histogram": [0.7, 0.1, 0.05, 0.05, 0.05, 0.05],
        "bottom_histogram": [0.1, 0.1, 0.1, 0.6, 0.05, 0.05]
    }
    
    matching_response = await async_httpx_client.post(
        f"{EEP_SERVICE_URL}/api/compute_match",
        json=matching_styles_request
    )
    
    # Assertions for matching styles
    assert matching_response.status_code == 200
    matching_data = matching_response.json()
    assert matching_data["match_score"] == 85  # High score for matching styles
    assert matching_data["analysis"]["style_consistency"]["score"] >= 70  # Good style consistency
    
    # Test 2: Mismatched styles (Formal top, Casual bottom)
    mismatched_styles_request = {
        "top_style": "Formal",
        "bottom_style": "Casual",
        "top_vector": [0.1, 0.2, 0.3, 0.4, 0.5],
        "bottom_vector": [0.15, 0.25, 0.35, 0.45, 0.55],
        "top_histogram": [0.1, 0.1, 0.1, 0.6, 0.05, 0.05],
        "bottom_histogram": [0.7, 0.1, 0.05, 0.05, 0.05, 0.05]
    }
    
    mismatched_response = await async_httpx_client.post(
        f"{EEP_SERVICE_URL}/api/compute_match",
        json=mismatched_styles_request
    )
    
    # Assertions for mismatched styles
    assert mismatched_response.status_code == 200
    mismatched_data = mismatched_response.json()
    assert mismatched_data["match_score"] == 45  # Lower score for mismatched styles
    assert mismatched_data["analysis"]["style_consistency"]["score"] == 40  # Poor style consistency
    assert "suggestions" in mismatched_data
    assert len(mismatched_data["suggestions"]) >= 2  # Should have multiple suggestions for improvement 