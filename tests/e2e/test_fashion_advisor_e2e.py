import pytest
import httpx
import os
import sys
import base64
import io
import time
import random
import asyncio
from pathlib import Path
from PIL import Image

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import from conftest
from conftest import (
    EEP_SERVICE_URL,
    MATCH_SERVICE_URL,
    VIRTUAL_TRYON_SERVICE_URL,
    TEST_DATA_DIR
)

# Mark all tests in this file as e2e tests
pytestmark = [pytest.mark.e2e, pytest.mark.live]

# Define the test images directory
TEST_IMAGES_DIR = Path(__file__).parent.parent / "data" / "test_images"

# Test image URLs for real-world testing
PERSON_IMAGE_URLS = [
    "https://raw.githubusercontent.com/zakarialabban/datasets/main/fashion/person_outfit.jpg",
    "https://res.cloudinary.com/dnl6nfcne/image/upload/v1713737644/fashion/person_casual_ybqhue.jpg",
    "https://res.cloudinary.com/dnl6nfcne/image/upload/v1713737644/fashion/person_formal_zlfmbx.jpg"
]

TOP_IMAGE_URLS = [
    "https://raw.githubusercontent.com/zakarialabban/datasets/main/fashion/tshirt_blue.jpg",
    "https://raw.githubusercontent.com/zakarialabban/datasets/main/fashion/shirt_white.jpg",
    "https://res.cloudinary.com/dnl6nfcne/image/upload/v1713737644/fashion/shirt_black_pu1s2z.jpg"
]

BOTTOM_IMAGE_URLS = [
    "https://raw.githubusercontent.com/zakarialabban/datasets/main/fashion/jeans_blue.jpg",
    "https://raw.githubusercontent.com/zakarialabban/datasets/main/fashion/pants_black.jpg",
    "https://res.cloudinary.com/dnl6nfcne/image/upload/v1713737644/fashion/jeans_dark_hxdkxw.jpg"
]

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

def save_test_image(image_bytes, filename):
    """Save image bytes to the test images directory."""
    os.makedirs(TEST_IMAGES_DIR, exist_ok=True)
    image_path = TEST_IMAGES_DIR / filename
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    print(f"Saved test image to {image_path}")
    return image_path

def load_test_image(filename):
    """Load an image from the test images directory."""
    image_path = TEST_IMAGES_DIR / filename
    if not image_path.exists():
        raise FileNotFoundError(f"Test image {filename} not found at {image_path}")
    
    with open(image_path, "rb") as f:
        return f.read()

@pytest.mark.asyncio
async def test_e2e_fashion_full_workflow(async_httpx_client):
    """
    End-to-end test for the complete fashion advisor workflow:
    1. Analyze a person's outfit to detect clothing items
    2. Get recommendations for one of the detected items
    3. Match a top and bottom to check outfit compatibility
    4. (Optional) Try on a virtual garment
    
    This test uses actual backend services and real images.
    """
    print("\n=== Starting End-to-End Fashion Advisor Test ===")
    
    # Step 1: Check if all required services are up
    print("\n--- Checking service health ---")
    try:
        # Check EEP service
        eep_health = await async_httpx_client.get(f"{EEP_SERVICE_URL}/health", timeout=5.0)
        print(f"EEP service health: {eep_health.status_code}")
        assert eep_health.status_code == 200, "EEP service is not healthy"
        
        # Check Match service
        match_health = await async_httpx_client.get(f"{MATCH_SERVICE_URL}/health", timeout=5.0)
        print(f"Match service health: {match_health.status_code}")
        assert match_health.status_code == 200, "Match service is not healthy"
        
        print("All services are healthy!")
    except Exception as e:
        pytest.skip(f"Service health check failed: {str(e)}")
    
    # Step 2: Get or download test images
    print("\n--- Preparing test images ---")
    
    # Try to use existing test images if available
    person_image_data = None
    top_image_data = None
    bottom_image_data = None
    
    try:
        person_files = list(TEST_IMAGES_DIR.glob("*person*.jpg"))
        top_files = list(TEST_IMAGES_DIR.glob("*shirt*.jpg")) + list(TEST_IMAGES_DIR.glob("*top*.jpg"))
        bottom_files = list(TEST_IMAGES_DIR.glob("*pants*.jpg")) + list(TEST_IMAGES_DIR.glob("*jeans*.jpg")) + list(TEST_IMAGES_DIR.glob("*bottom*.jpg"))
        
        if person_files and top_files and bottom_files:
            print("Using existing test images")
            person_image_path = random.choice(person_files)
            top_image_path = random.choice(top_files)
            bottom_image_path = random.choice(bottom_files)
            
            print(f"Person image: {person_image_path.name}")
            print(f"Top image: {top_image_path.name}")
            print(f"Bottom image: {bottom_image_path.name}")
            
            person_image_data = load_test_image(person_image_path.name)
            top_image_data = load_test_image(top_image_path.name)
            bottom_image_data = load_test_image(bottom_image_path.name)
        else:
            print("Downloading test images")
            person_url = random.choice(PERSON_IMAGE_URLS)
            top_url = random.choice(TOP_IMAGE_URLS)
            bottom_url = random.choice(BOTTOM_IMAGE_URLS)
            
            person_filename = f"e2e_person_{int(time.time())}.jpg"
            top_filename = f"e2e_top_{int(time.time())}.jpg"
            bottom_filename = f"e2e_bottom_{int(time.time())}.jpg"
            
            person_image_data = await download_test_image(person_url, async_httpx_client, person_filename)
            top_image_data = await download_test_image(top_url, async_httpx_client, top_filename)
            bottom_image_data = await download_test_image(bottom_url, async_httpx_client, bottom_filename)
            
            print(f"Downloaded person image: {len(person_image_data)} bytes")
            print(f"Downloaded top image: {len(top_image_data)} bytes")
            print(f"Downloaded bottom image: {len(bottom_image_data)} bytes")
    except Exception as e:
        pytest.skip(f"Failed to prepare test images: {str(e)}")
    
    # Step 3: Analyze the person image to detect clothing
    print("\n--- Step 1: Analyzing person image to detect clothing ---")
    
    analyze_files = {
        'file': ('person.jpg', person_image_data, 'image/jpeg')
    }
    
    analyze_response = await async_httpx_client.post(
        f"{EEP_SERVICE_URL}/analyze",
        files=analyze_files,
        headers={"Accept": "application/json"},
        timeout=60.0
    )
    
    print(f"Analyze response status: {analyze_response.status_code}")
    assert analyze_response.status_code == 200, "Analyze request failed"
    
    try:
        analyze_data = analyze_response.json()
        print("Successfully parsed analyze response as JSON")
    except Exception as e:
        # If JSON parsing fails, we might have received HTML
        print(f"Failed to parse as JSON: {str(e)}")
        if "<!DOCTYPE html>" in analyze_response.text:
            print("Response appears to be HTML, extracting data...")
            import re
            
            # Extract request_id
            request_id_match = re.search(r'name="request_id"\s+value="([^"]+)"', analyze_response.text)
            request_id = request_id_match.group(1) if request_id_match else None
            
            # Extract detection info
            detection_matches = re.findall(r'<h3>([^<]+)\s+\(Confidence:\s+([\d.]+)\)</h3>', analyze_response.text)
            
            analyze_data = {
                "request_id": request_id,
                "detections": [
                    {
                        "class_name": class_name.strip(),
                        "confidence": float(confidence),
                        "detection_id": i
                    } for i, (class_name, confidence) in enumerate(detection_matches)
                ],
                "original_image_path": "",
                "processing_time": 0,
                "timestamp": ""
            }
            
            print(f"Extracted request_id: {request_id}")
            print(f"Extracted {len(analyze_data['detections'])} detections")
        else:
            pytest.fail(f"Could not parse analyze response: {str(e)}")
    
    # Verify we have detections
    assert "detections" in analyze_data, "No detections field in response"
    assert analyze_data["detections"], "No clothing items detected in the person image"
    
    print(f"Detected {len(analyze_data['detections'])} clothing items:")
    for i, item in enumerate(analyze_data["detections"]):
        item_class = item.get("class_name", "unknown")
        item_confidence = item.get("confidence", 0)
        print(f"  Item {i+1}: {item_class} (confidence: {item_confidence:.2f})")
    
    # Step 4: Get recommendations for one of the detected items
    print("\n--- Step 2: Getting recommendations for a detected item ---")
    
    # Find a suitable item for recommendations
    suitable_item = None
    item_type = None
    
    for item in analyze_data["detections"]:
        class_name = item.get("class_name", "").lower()
        
        if "shirt" in class_name or "top" in class_name or "tshirt" in class_name or "jacket" in class_name:
            suitable_item = item
            item_type = "topwear"
            break
        elif "pant" in class_name or "short" in class_name or "jean" in class_name or "skirt" in class_name:
            suitable_item = item
            item_type = "bottomwear"
            break
    
    if not suitable_item:
        print("No suitable clothing item found for recommendations, using the first item")
        suitable_item = analyze_data["detections"][0]
        class_name = suitable_item.get("class_name", "").lower()
        item_type = "topwear" if any(word in class_name for word in ["shirt", "top", "tshirt", "jacket"]) else "bottomwear"
    
    print(f"Using {suitable_item.get('class_name')} for recommendations (type: {item_type})")
    
    # Get the request_id and detection_id
    request_id = analyze_data.get("request_id")
    detection_id = analyze_data["detections"].index(suitable_item)
    
    # Prepare recommendation request
    recommendation_request = {
        "request_id": request_id,
        "detection_id": str(detection_id),
        "operation": "similarity",  # "similarity" or "matching"
        "item_type": item_type
    }
    
    print(f"Recommendation request: {recommendation_request}")
    
    recommendation_response = await async_httpx_client.post(
        f"{EEP_SERVICE_URL}/api/recommendation",
        json=recommendation_request,
        timeout=60.0
    )
    
    print(f"Recommendation response status: {recommendation_response.status_code}")
    assert recommendation_response.status_code == 200, "Recommendation request failed"
    
    recommendation_data = recommendation_response.json()
    
    # Verify recommendation response structure
    assert "image_data" in recommendation_data, "No image_data in recommendation response"
    assert "content_type" in recommendation_data, "No content_type in recommendation response"
    assert recommendation_data["content_type"] == "image/jpeg", f"Unexpected content type: {recommendation_data['content_type']}"
    
    # Save the recommendation image
    try:
        reco_image_bytes = base64.b64decode(recommendation_data["image_data"])
        reco_filename = f"e2e_recommendation_{int(time.time())}.jpg"
        save_test_image(reco_image_bytes, reco_filename)
        print(f"Saved recommendation image: {reco_filename}")
    except Exception as e:
        print(f"Warning: Could not save recommendation image: {str(e)}")
    
    # Step 5: Match top and bottom items
    print("\n--- Step 3: Matching top and bottom items ---")
    
    match_files = {
        'topwear': ('top.jpg', top_image_data, 'image/jpeg'),
        'bottomwear': ('bottom.jpg', bottom_image_data, 'image/jpeg')
    }
    
    match_response = await async_httpx_client.post(
        f"{MATCH_SERVICE_URL}/match",
        files=match_files,
        timeout=60.0
    )
    
    print(f"Match response status: {match_response.status_code}")
    assert match_response.status_code == 200, "Match request failed"
    
    match_data = match_response.json()
    
    # Verify match response structure
    assert "match_score" in match_data, "No match_score in match response"
    assert "analysis" in match_data, "No analysis in match response"
    assert "suggestions" in match_data, "No suggestions in match response"
    
    print(f"Match score: {match_data['match_score']}")
    print("Analysis:")
    for component, details in match_data["analysis"].items():
        if isinstance(details, dict) and "score" in details and "analysis" in details:
            print(f"  {component}: {details['score']} - {details['analysis']}")
    
    print("Suggestions:")
    for suggestion in match_data["suggestions"]:
        print(f"  - {suggestion}")
    
    # Optional Step 6: Virtual Try-On (if available)
    try:
        print("\n--- Step 4: Testing Virtual Try-On (Optional) ---")
        
        # Check if virtual try-on service is available
        tryon_health = await async_httpx_client.get(f"{VIRTUAL_TRYON_SERVICE_URL}/health", timeout=5.0)
        if tryon_health.status_code != 200:
            print(f"Virtual try-on service is not available, skipping this step")
        else:
            print("Virtual try-on service is available, proceeding with try-on test")
            
            tryon_files = {
                'model_image': ('model.jpg', person_image_data, 'image/jpeg'),
                'garment_image': ('garment.jpg', top_image_data, 'image/jpeg')
            }
            
            tryon_response = await async_httpx_client.post(
                f"{VIRTUAL_TRYON_SERVICE_URL}/tryon",
                files=tryon_files,
                data={"category": "upper_body", "mode": "quality"},
                timeout=120.0  # Virtual try-on can take longer
            )
            
            print(f"Try-on response status: {tryon_response.status_code}")
            
            if tryon_response.status_code == 200:
                # Try to parse response and save the result image
                try:
                    if "image/jpeg" in tryon_response.headers.get('content-type', ''):
                        # Direct image response
                        tryon_image_bytes = tryon_response.content
                    elif "application/json" in tryon_response.headers.get('content-type', ''):
                        # JSON response with base64-encoded image
                        tryon_data = tryon_response.json()
                        if "image_data" in tryon_data:
                            tryon_image_bytes = base64.b64decode(tryon_data["image_data"])
                        else:
                            print("No image data in try-on response")
                            tryon_image_bytes = None
                    else:
                        # HTML response or other format
                        print(f"Unexpected try-on response format: {tryon_response.headers.get('content-type')}")
                        tryon_image_bytes = None
                    
                    if tryon_image_bytes:
                        tryon_filename = f"e2e_tryon_{int(time.time())}.jpg"
                        save_test_image(tryon_image_bytes, tryon_filename)
                        print(f"Saved try-on result image: {tryon_filename}")
                except Exception as e:
                    print(f"Warning: Could not process try-on result: {str(e)}")
            else:
                print(f"Try-on request failed with status {tryon_response.status_code}")
    except Exception as e:
        print(f"Virtual try-on test failed: {str(e)}")
        print("Skipping try-on step")
    
    print("\n=== End-to-End Fashion Advisor Test Completed Successfully ===") 