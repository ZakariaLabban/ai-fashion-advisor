import pytest
import httpx
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import from conftest
from conftest import EEP_SERVICE_URL, encode_image_base64

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

@pytest.fixture
def sample_person_image():
    """Create a sample image with a person for testing."""
    return b"mock_person_image_data"

@pytest.mark.asyncio
async def test_analyze_pipeline_integration(async_httpx_client, monkeypatch, sample_person_image):
    """
    Integration test for the full analysis pipeline.
    
    This test mocks the responses from the EEP, which internally would call:
    1. Detection IEP
    2. Style IEP
    3. Feature IEP
    """
    # Mock the response from the EEP
    async def mock_post(*args, **kwargs):
        # Construct a realistic response that would come from the full pipeline
        response_data = {
            "request_id": "test-integration-123",
            "original_image_path": "/static/uploads/test_person.jpg",
            "annotated_image_path": "/static/results/test_person_annotated.jpg",
            "detections": [
                {
                    "class_name": "Shirt",
                    "class_id": 4,
                    "confidence": 0.92,
                    "bbox": [125, 100, 175, 350],
                    "crop_path": "/static/results/test_integration-123_Shirt_0.jpg",
                    "features": [0.1, 0.2, 0.3, 0.4, 0.5, -0.1, -0.2, -0.3],
                    "color_histogram": [0.7, 0.1, 0.05, 0.05, 0.05, 0.05]
                },
                {
                    "class_name": "Pants/Shorts",
                    "class_id": 10,
                    "confidence": 0.88,
                    "bbox": [125, 350, 175, 550],
                    "crop_path": "/static/results/test_integration-123_Pants_1.jpg",
                    "features": [0.2, 0.3, 0.4, 0.5, 0.6, -0.2, -0.3, -0.4],
                    "color_histogram": [0.1, 0.1, 0.1, 0.6, 0.05, 0.05]
                }
            ],
            "styles": [
                {
                    "style_name": "Casual",
                    "style_id": 1,
                    "confidence": 0.85
                },
                {
                    "style_name": "Sporty",
                    "style_id": 3,
                    "confidence": 0.62
                }
            ],
            "processing_time": 2.35,
            "timestamp": "2023-05-20T15:30:45.123456"
        }
        
        response = httpx.Response(200, json=response_data)
        return response
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Prepare the request
    files = {
        'file': ('person.jpg', sample_person_image, 'image/jpeg')
    }
    
    # Make the request to the analyze endpoint
    response = await async_httpx_client.post(
        f"{EEP_SERVICE_URL}/api/analyze",
        files=files
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    
    # Check structure of the response
    assert "request_id" in data
    assert "original_image_path" in data
    assert "annotated_image_path" in data
    assert "detections" in data
    assert "styles" in data
    assert "processing_time" in data
    assert "timestamp" in data
    
    # Check detections
    assert len(data["detections"]) == 2
    shirt = next((d for d in data["detections"] if d["class_name"] == "Shirt"), None)
    pants = next((d for d in data["detections"] if d["class_name"] == "Pants/Shorts"), None)
    assert shirt is not None
    assert pants is not None
    
    # Check detection details
    assert "bbox" in shirt
    assert "confidence" in shirt
    assert "features" in shirt
    assert "color_histogram" in shirt
    
    # Check styles
    assert len(data["styles"]) == 2
    casual = next((s for s in data["styles"] if s["style_name"] == "Casual"), None)
    sporty = next((s for s in data["styles"] if s["style_name"] == "Sporty"), None)
    assert casual is not None
    assert sporty is not None
    
    # Check style details
    assert casual["confidence"] > sporty["confidence"]  # Casual should be more confident

@pytest.mark.asyncio
async def test_analyze_to_recommendation_flow(async_httpx_client, monkeypatch, sample_person_image):
    """
    Integration test for the analyze → recommendation flow.
    
    This tests the flow where a user:
    1. Analyzes an outfit image
    2. Selects one of the detected items
    3. Requests recommendations for similar or matching items
    """
    # Track request state across different calls
    request_state = {
        "current_step": "analyze",  # Will change to "recommendation" after first call
        "request_id": "test-integration-456",
        "selected_detection_id": "0"  # Shirt with index 0
    }
    
    # Mock the response for both analyze and recommendation
    async def mock_post(*args, **kwargs):
        url = args[0]
        
        if "analyze" in url and request_state["current_step"] == "analyze":
            # First call - analyze response
            analyze_response = {
                "request_id": request_state["request_id"],
                "original_image_path": "/static/uploads/test_person.jpg",
                "annotated_image_path": "/static/results/test_person_annotated.jpg",
                "detections": [
                    {
                        "class_name": "Shirt",
                        "class_id": 4,
                        "confidence": 0.92,
                        "bbox": [125, 100, 175, 350],
                        "crop_path": "/static/results/test_integration-456_Shirt_0.jpg",
                        "features": [0.1, 0.2, 0.3, 0.4, 0.5, -0.1, -0.2, -0.3],
                        "color_histogram": [0.7, 0.1, 0.05, 0.05, 0.05, 0.05]
                    }
                ],
                "styles": [
                    {
                        "style_name": "Casual",
                        "style_id": 1,
                        "confidence": 0.85
                    }
                ],
                "processing_time": 1.75,
                "timestamp": "2023-05-20T15:45:30.123456"
            }
            
            # Update state for next call
            request_state["current_step"] = "recommendation"
            
            return httpx.Response(200, json=analyze_response)
            
        elif "recommendation" in url and request_state["current_step"] == "recommendation":
            # Second call - recommendation response
            # Check request parameters
            request_json = kwargs.get("json", {})
            
            # Verify request format
            assert "request_id" in request_json
            assert "detection_id" in request_json
            assert "operation" in request_json
            assert "item_type" in request_json
            
            # Get the item type - should be "topwear" for the reco system
            item_type = request_json.get("item_type")
            
            recommendation_response = {
                "request_id": request_state["request_id"],
                "detection_id": request_state["selected_detection_id"],
                "operation": request_json["operation"],
                "item_type": item_type,
                "matches": [
                    {
                        "item_id": "match1",
                        "similarity_score": 0.92,
                        "image_url": "/static/results/recommendation_1.jpg",
                        "metadata": {
                            "style": "Casual",
                            "color": "Blue",
                            "type": "Pants/Shorts" if item_type == "topwear" else "Shirt"
                        }
                    },
                    {
                        "item_id": "match2",
                        "similarity_score": 0.85,
                        "image_url": "/static/results/recommendation_2.jpg",
                        "metadata": {
                            "style": "Casual",
                            "color": "Black",
                            "type": "Pants/Shorts" if item_type == "topwear" else "Shirt"
                        }
                    }
                ],
                "processing_time": 0.95
            }
            
            return httpx.Response(200, json=recommendation_response)
        
        # Default response for unexpected calls
        return httpx.Response(404, json={"error": "Not found"})
    
    # Apply the mock
    monkeypatch.setattr(async_httpx_client, "post", mock_post)
    
    # Step 1: Analyze the image
    files = {
        'file': ('person.jpg', sample_person_image, 'image/jpeg')
    }
    
    analyze_response = await async_httpx_client.post(
        f"{EEP_SERVICE_URL}/api/analyze",
        files=files
    )
    
    # Check analyze response
    assert analyze_response.status_code == 200
    analyze_data = analyze_response.json()
    assert analyze_data["request_id"] == request_state["request_id"]
    assert len(analyze_data["detections"]) == 1
    assert analyze_data["detections"][0]["class_name"] == "Shirt"
    
    # Step 2: Get recommendations for the detected item
    # Use "topwear" instead of "tops" to match the recommendation system's expected values
    recommendation_request = {
        "request_id": request_state["request_id"],
        "detection_id": request_state["selected_detection_id"],
        "operation": "matching",
        "item_type": "topwear"
    }
    
    recommendation_response = await async_httpx_client.post(
        f"{EEP_SERVICE_URL}/api/recommendation",
        json=recommendation_request
    )
    
    # Check recommendation response
    assert recommendation_response.status_code == 200
    recommendation_data = recommendation_response.json()
    assert recommendation_data["request_id"] == request_state["request_id"]
    assert recommendation_data["detection_id"] == request_state["selected_detection_id"]
    assert recommendation_data["operation"] == "matching"
    assert recommendation_data["item_type"] == "topwear"
    assert len(recommendation_data["matches"]) == 2 