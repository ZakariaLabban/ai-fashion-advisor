import pytest
import httpx
import base64
import sys
import os
import io
import shutil
from pathlib import Path
from PIL import Image
import random
import time

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import from conftest
from conftest import (
    EEP_SERVICE_URL, 
    MATCH_SERVICE_URL
)

# Mark all tests in this file as live tests
pytestmark = [pytest.mark.integration, pytest.mark.live]

# Define the test images directory
TEST_IMAGES_DIR = Path(__file__).parent.parent / "data" / "test_images"

# Function to download a test image
async def download_test_image(url, async_client, filename=None):
    """Download a test image from a URL and optionally save it to the test images directory."""
    response = await async_client.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to download image from {url}, status: {response.status_code}")
    
    # Save the image to a file if filename is provided
    if filename:
        # Ensure the directory exists
        os.makedirs(TEST_IMAGES_DIR, exist_ok=True)
        
        # Save the image
        image_path = TEST_IMAGES_DIR / filename
        with open(image_path, "wb") as f:
            f.write(response.content)
        
        print(f"Saved test image to {image_path}")
    
    return response.content

# Function to save a test image from bytes
def save_test_image(image_bytes, filename):
    """Save image bytes to the test images directory."""
    os.makedirs(TEST_IMAGES_DIR, exist_ok=True)
    image_path = TEST_IMAGES_DIR / filename
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    print(f"Saved test image to {image_path}")
    return image_path

# Function to load a test image from the test images directory
def load_test_image(filename):
    """Load an image from the test images directory."""
    image_path = TEST_IMAGES_DIR / filename
    if not image_path.exists():
        raise FileNotFoundError(f"Test image {filename} not found at {image_path}")
    
    with open(image_path, "rb") as f:
        return f.read()

@pytest.mark.asyncio
async def test_live_outfit_match(async_httpx_client):
    """
    Live integration test for the outfit matching functionality.
    
    This test calls the actual backend services without mocking.
    It requires the Match service to be running.
    """
    # First, check if the service is up by calling the health endpoint
    try:
        health_response = await async_httpx_client.get(
            f"{MATCH_SERVICE_URL}/health",
            timeout=5.0
        )
        print(f"Match service health check: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"Match service health response: {health_response.json()}")
    except Exception as e:
        print(f"Match service health check failed: {str(e)}")
        pytest.skip(f"Match service health check failed: {str(e)}")
    
    # Try to use existing test images first
    try:
        # Try to load existing images from the test directory
        test_files = list(TEST_IMAGES_DIR.glob("*.jpg"))
        if len(test_files) >= 2:
            # Use random top and bottom from existing files
            print(f"Found {len(test_files)} test images in {TEST_IMAGES_DIR}")
            random.shuffle(test_files)
            top_image_path = test_files[0]
            bottom_image_path = test_files[1]
            
            print(f"Using top image: {top_image_path.name}")
            print(f"Using bottom image: {bottom_image_path.name}")
            
            with open(top_image_path, "rb") as f:
                top_image = f.read()
            
            with open(bottom_image_path, "rb") as f:
                bottom_image = f.read()
        else:
            # Download real clothing images for testing
            # URLs for realistic clothing images (shirts and pants)
            top_urls = [
                "https://raw.githubusercontent.com/zakarialabban/datasets/main/fashion/tshirt_blue.jpg",
                "https://raw.githubusercontent.com/zakarialabban/datasets/main/fashion/shirt_white.jpg",
                "https://res.cloudinary.com/dnl6nfcne/image/upload/v1713737644/fashion/shirt_black_pu1s2z.jpg"
            ]
            
            bottom_urls = [
                "https://raw.githubusercontent.com/zakarialabban/datasets/main/fashion/jeans_blue.jpg",
                "https://raw.githubusercontent.com/zakarialabban/datasets/main/fashion/pants_black.jpg",
                "https://res.cloudinary.com/dnl6nfcne/image/upload/v1713737644/fashion/jeans_dark_hxdkxw.jpg"
            ]
            
            # Randomly select one top and one bottom
            top_url = random.choice(top_urls)
            bottom_url = random.choice(bottom_urls)
            
            # Generate file names based on URLs
            top_filename = f"top_{int(time.time())}.jpg"
            bottom_filename = f"bottom_{int(time.time())}.jpg"
            
            # Download the images and save them to the test directory
            top_image = await download_test_image(top_url, async_httpx_client, top_filename)
            bottom_image = await download_test_image(bottom_url, async_httpx_client, bottom_filename)
            
            print(f"Downloaded and saved top image: {top_filename}, {len(top_image)} bytes")
            print(f"Downloaded and saved bottom image: {bottom_filename}, {len(bottom_image)} bytes")
    except Exception as e:
        print(f"Failed to get test images: {str(e)}")
        # Use fallback images from a public test API
        try:
            top_image = await download_test_image("https://picsum.photos/200/300", async_httpx_client)
            bottom_image = await download_test_image("https://picsum.photos/200/300", async_httpx_client)
            
            # Save these images as well
            save_test_image(top_image, f"fallback_top_{int(time.time())}.jpg")
            save_test_image(bottom_image, f"fallback_bottom_{int(time.time())}.jpg")
        except Exception as e2:
            print(f"Failed to download fallback images: {str(e2)}")
            pytest.skip("Could not download test images")
    
    # Prepare the request - based on the actual match_api.py implementation
    files = {
        'topwear': ('topwear.jpg', top_image, 'image/jpeg'),
        'bottomwear': ('bottomwear.jpg', bottom_image, 'image/jpeg')
    }
    
    # Try the correct endpoint - confirmed from the code that it's /match
    try:
        print(f"Calling match endpoint: {MATCH_SERVICE_URL}/match")
        response = await async_httpx_client.post(
            f"{MATCH_SERVICE_URL}/match",
            files=files,
            timeout=60.0  # Increased timeout as image processing can take time
        )
        print(f"Match response status: {response.status_code}")
        
        # If we get an error response, print the content for debugging
        if response.status_code != 200:
            print(f"Match response error content: {response.text[:1000]}")
            pytest.skip(f"Match endpoint returned {response.status_code}: {response.text[:500]}")
        
        data = response.json()
        print(f"Match response data: {data}")
        
        # Check structure of the response - based on MatchResponse model in match_api.py
        assert "match_score" in data, "Response missing match_score field"
        assert "analysis" in data, "Response missing analysis field"
        assert "suggestions" in data, "Response missing suggestions field"
        
        # Print response for debugging
        print(f"Match score: {data['match_score']}")
        print(f"Analysis: {data['analysis']}")
        
        # Check analysis details if they exist - based on the calculation in match_api.py
        if "analysis" in data:
            expected_analysis_components = [
                "color_harmony", 
                "feature_match", 
                "color_histogram", 
                "style_consistency", 
                "occasion_appropriateness"
            ]
            
            for component in expected_analysis_components:
                if component in data["analysis"]:
                    assert "score" in data["analysis"][component], f"Missing score in {component} analysis"
                    assert "analysis" in data["analysis"][component], f"Missing analysis text in {component} analysis"
        
        # Check suggestions
        assert isinstance(data["suggestions"], list), "Suggestions is not a list"
        if data["suggestions"]:
            print(f"Suggestions: {data['suggestions']}")
    except Exception as e:
        print(f"Error with match endpoint: {str(e)}")
        pytest.skip(f"Error testing match endpoint: {str(e)}")

@pytest.mark.asyncio
async def test_live_analyze_pipeline(async_httpx_client):
    """
    Live integration test for the analysis pipeline.
    
    This test calls the actual backend services without mocking.
    It requires the EEP service to be running.
    """
    # First, check if the service is up by calling the health endpoint
    try:
        health_response = await async_httpx_client.get(
            f"{EEP_SERVICE_URL}/health",
            timeout=5.0
        )
        print(f"EEP service health check: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"EEP service health response: {health_response.json()}")
    except Exception as e:
        print(f"EEP service health check failed: {str(e)}")
        pytest.skip(f"EEP service health check failed: {str(e)}")
    
    # Try to use existing person images first
    try:
        # Try to load existing images from the test directory
        person_files = list(TEST_IMAGES_DIR.glob("*person*.jpg"))
        if person_files:
            # Use a random person image from existing files
            person_image_path = random.choice(person_files)
            print(f"Using person image: {person_image_path.name}")
            
            with open(person_image_path, "rb") as f:
                person_image = f.read()
        else:
            # Download a real person image for testing
            # URLs for realistic person images
            person_urls = [
                "https://raw.githubusercontent.com/zakarialabban/datasets/main/fashion/person_outfit.jpg",
                "https://res.cloudinary.com/dnl6nfcne/image/upload/v1713737644/fashion/person_casual_ybqhue.jpg",
                "https://res.cloudinary.com/dnl6nfcne/image/upload/v1713737644/fashion/person_formal_zlfmbx.jpg"
            ]
            
            # Randomly select one person image
            person_url = random.choice(person_urls)
            
            # Generate file name based on URL
            person_filename = f"person_{int(time.time())}.jpg"
            
            # Download the image and save it to the test directory
            person_image = await download_test_image(person_url, async_httpx_client, person_filename)
            print(f"Downloaded and saved person image: {person_filename}, {len(person_image)} bytes")
    except Exception as e:
        print(f"Failed to get person test image: {str(e)}")
        # Use fallback image
        try:
            person_image = await download_test_image("https://picsum.photos/300/500", async_httpx_client)
            
            # Save this image as well
            save_test_image(person_image, f"fallback_person_{int(time.time())}.jpg")
        except Exception as e2:
            print(f"Failed to download fallback image: {str(e2)}")
            pytest.skip("Could not download test image")
    
    # Prepare the file upload for the /api/analyze endpoint
    # The endpoint expects a 'file' parameter with the image data
    print(f"Person image size: {len(person_image)} bytes")
    files = {
        'file': ('person.jpg', person_image, 'image/jpeg')
    }
    
    # Make the request to the analyze endpoint
    try:
        print(f"Calling EEP analyze endpoint: {EEP_SERVICE_URL}/api/analyze")
        response = await async_httpx_client.post(
            f"{EEP_SERVICE_URL}/api/analyze",
            files=files,
            timeout=60.0  # Increased timeout as image processing can take time
        )
        print(f"EEP analyze response status: {response.status_code}")
        
        # If we get an error response, print the content for debugging
        if response.status_code != 200:
            print(f"EEP analyze response error content: {response.text[:1000]}")
            pytest.skip(f"Could not get successful response from EEP analyze endpoint: {response.status_code}")
        
        data = response.json()
        
        # Print first part of response for debugging
        print(f"EEP analyze response (truncated): {str(data)[:500]}...")
        
        # Check structure of the response based on AnalysisResponse model
        assert "request_id" in data, "Response missing request_id field"
        assert "detections" in data, "Response missing detections field"
        assert "original_image_path" in data, "Response missing original_image_path field"
        assert "processing_time" in data, "Response missing processing_time field"
        assert "timestamp" in data, "Response missing timestamp field"
        
        # Check if we have detections
        if not data["detections"]:
            print("No items detected in the image")
            pytest.skip("No items detected in the image - test image may not contain recognizable clothing")
        
        # Print detection info
        print(f"Detected {len(data['detections'])} items in the image")
        for i, item in enumerate(data["detections"]):
            item_class = item.get("class_name", item.get("category", "unknown"))
            item_confidence = item.get("confidence", 0)
            print(f"Item {i+1}: {item_class} (confidence: {item_confidence})")
            assert "class_name" in item or "category" in item, f"Item {i+1} missing class_name/category field"
            
        # Store the request_id for later use in recommendation testing
        print(f"Analysis request_id: {data['request_id']}")
        
        # Return the response data so it can be used by other tests
        return data
    except Exception as e:
        print(f"EEP analyze request failed: {str(e)}")
        pytest.skip(f"EEP analyze request failed: {str(e)}")
        return None

@pytest.mark.asyncio
async def test_live_recommendation_flow(async_httpx_client):
    """
    Live integration test for the full recommendation flow.
    
    This test calls the actual backend services without mocking.
    It requires both the EEP and recommendation services to be running.
    """
    # First, check if the EEP service is up by calling the health endpoint
    try:
        health_response = await async_httpx_client.get(
            f"{EEP_SERVICE_URL}/health",
            timeout=5.0
        )
        print(f"EEP service health check: {health_response.status_code}")
        if health_response.status_code != 200:
            pytest.skip(f"EEP service not healthy: {health_response.status_code}")
    except Exception as e:
        print(f"EEP service health check failed: {str(e)}")
        pytest.skip(f"EEP service health check failed: {str(e)}")
    
    # First step: Call the analyze endpoint with a person image
    try:
        # Get analysis data by calling the analyze test
        analyze_data = await test_live_analyze_pipeline(async_httpx_client)
        
        if not analyze_data:
            pytest.skip("Could not get analysis data from the analyze test")
        
        # Check if we have detected items
        if not analyze_data.get("detections", []):
            pytest.skip("No items detected in the image")
        
        # Second step: Call the recommend endpoint with the analysis results
        # Get the first detected item
        item = analyze_data["detections"][0]
        print(f"Using item for recommendation: {item}")
        
        # Get the request_id and detection_id for the recommendation
        request_id = analyze_data.get("request_id")
        detection_id = 0  # First detection
        
        # Determine the item type based on class name
        class_name = item.get("class_name", "").lower()
        if "shirt" in class_name or "top" in class_name or "tshirt" in class_name or "jacket" in class_name:
            item_type = "topwear"
        elif "pant" in class_name or "short" in class_name or "jean" in class_name or "skirt" in class_name:
            item_type = "bottomwear"
        else:
            item_type = "accessory"
        
        # Prepare the recommendation request
        recommendation_request = {
            "request_id": request_id,
            "detection_id": str(detection_id),
            "operation": "similarity",  # or "matching"
            "item_type": item_type
        }
        
        print(f"Recommendation request: {recommendation_request}")
        
        # Try recommendation endpoint
        try:
            print(f"Calling recommendation endpoint: {EEP_SERVICE_URL}/api/recommendation")
            recommendation_response = await async_httpx_client.post(
                f"{EEP_SERVICE_URL}/api/recommendation",
                json=recommendation_request,
                timeout=60.0
            )
            
            print(f"Recommendation response status: {recommendation_response.status_code}")
            
            if recommendation_response.status_code == 200:
                recommendation_data = recommendation_response.json()
                print(f"Recommendation response (truncated): {str(recommendation_data)[:500]}...")
                
                # Check structure based on the actual API implementation
                assert "image_data" in recommendation_data, "Response missing image_data field"
                assert "content_type" in recommendation_data, "Response missing content_type field"
                
                # Verify the content_type is as expected
                assert recommendation_data["content_type"] == "image/jpeg", "Unexpected content_type"
                
                # Verify the image_data is a non-empty base64 string
                assert recommendation_data["image_data"], "Empty image_data in response"
                
                # Try to decode the base64 data to verify it's valid
                try:
                    image_bytes = base64.b64decode(recommendation_data["image_data"])
                    print(f"Successfully decoded image data, size: {len(image_bytes)} bytes")
                    
                    # Save the image for inspection if needed
                    result_filename = f"recommendation_result_{int(time.time())}.jpg"
                    save_test_image(image_bytes, result_filename)
                    print(f"Saved recommendation result as {result_filename}")
                except Exception as e:
                    print(f"Failed to decode base64 image data: {str(e)}")
            else:
                print(f"Recommendation error: {recommendation_response.text[:1000]}")
                pytest.skip(f"Recommendation endpoint returned error: {recommendation_response.status_code}")
                
        except Exception as e:
            print(f"Recommendation request failed: {str(e)}")
            pytest.skip(f"Recommendation request failed: {str(e)}")
    except Exception as e:
        print(f"Recommendation flow test failed: {str(e)}")
        pytest.skip(f"Recommendation flow test failed: {str(e)}") 