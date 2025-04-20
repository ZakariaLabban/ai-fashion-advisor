import pytest
import httpx
import base64
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import from conftest
from conftest import (
    EEP_SERVICE_URL, 
    MATCH_SERVICE_URL, 
    sample_tshirt_image, 
    sample_pants_image,
    sample_person_image
)

# Mark all tests in this file as live tests
pytestmark = [pytest.mark.integration, pytest.mark.live]

@pytest.mark.asyncio
async def test_live_outfit_match(async_httpx_client, sample_tshirt_image, sample_pants_image):
    """
    Live integration test for the outfit matching functionality.
    
    This test calls the actual backend services without mocking.
    It requires the Match service to be running.
    """
    # Prepare the request
    files = {
        'topwear': ('tshirt.jpg', sample_tshirt_image, 'image/jpeg'),
        'bottomwear': ('pants.jpg', sample_pants_image, 'image/jpeg')
    }
    
    # Make the request to the match endpoint
    response = await async_httpx_client.post(
        f"{MATCH_SERVICE_URL}/api/match",
        files=files,
        timeout=30.0  # Increase timeout for real service
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
    
    # Print response for debugging
    print(f"Live match response: {data}")
    
    # Check analysis details
    assert "topwear" in data["analysis"]
    assert "bottomwear" in data["analysis"]

@pytest.mark.asyncio
async def test_live_analyze_pipeline(async_httpx_client, sample_person_image):
    """
    Live integration test for the analysis pipeline.
    
    This test calls the actual backend services without mocking.
    It requires the EEP service to be running.
    """
    # Encode the image for the request
    image_base64 = base64.b64encode(sample_person_image).decode('utf-8')
    
    # Prepare the request
    request_data = {
        "image": image_base64,
        "analyze_options": {
            "detect_clothes": True,
            "classify_style": True,
            "extract_features": True
        }
    }
    
    # Make the request to the analyze endpoint
    response = await async_httpx_client.post(
        f"{EEP_SERVICE_URL}/api/analyze",
        json=request_data,
        timeout=30.0  # Increase timeout for real service
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    
    # Print response for debugging
    print(f"Live analyze response: {data}")
    
    # Check structure of the response
    assert "request_id" in data
    assert "detected_items" in data
    
    # There should be some detected items in the image
    assert len(data["detected_items"]) > 0
    
    # Check that each item has style and features information
    for item in data["detected_items"]:
        assert "category" in item
        assert "style" in item
        assert "features" in item

@pytest.mark.asyncio
async def test_live_recommendation_flow(async_httpx_client, sample_person_image):
    """
    Live integration test for the full recommendation flow.
    
    This test calls the actual backend services without mocking.
    It requires both the EEP and recommendation services to be running.
    """
    # First, analyze the outfit
    image_base64 = base64.b64encode(sample_person_image).decode('utf-8')
    analyze_request = {
        "image": image_base64,
        "analyze_options": {
            "detect_clothes": True,
            "classify_style": True,
            "extract_features": True
        }
    }
    
    analyze_response = await async_httpx_client.post(
        f"{EEP_SERVICE_URL}/api/analyze",
        json=analyze_request,
        timeout=30.0
    )
    
    assert analyze_response.status_code == 200
    analyze_data = analyze_response.json()
    
    # Then, get recommendations based on the analysis
    if analyze_data["detected_items"]:
        # Get the first item's style and features
        item = analyze_data["detected_items"][0]
        
        recommendation_request = {
            "gender": "unisex",  # Default to unisex
            "style": item["style"]["name"] if "style" in item and "name" in item["style"] else "Casual",
            "category": item["category"],
            "vector": item["features"]["vector"] if "features" in item and "vector" in item["features"] else [0.1] * 5
        }
        
        # Request recommendations
        recommendation_response = await async_httpx_client.post(
            f"{EEP_SERVICE_URL}/api/recommend",
            json=recommendation_request,
            timeout=30.0
        )
        
        # Assertions for recommendation
        assert recommendation_response.status_code == 200
        recommendation_data = recommendation_response.json()
        
        # Print response for debugging
        print(f"Live recommendation response: {recommendation_data}")
        
        # Check structure
        assert "request_id" in recommendation_data
        assert "recommendations" in recommendation_data
        
        # Should have at least one recommendation
        if "recommendations" in recommendation_data:
            assert len(recommendation_data["recommendations"]) > 0 