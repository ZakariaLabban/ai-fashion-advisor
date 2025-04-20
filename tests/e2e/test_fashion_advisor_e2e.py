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
import aiohttp

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import from conftest
from conftest import (
    EEP_SERVICE_URL,
    MATCH_SERVICE_URL,
    VIRTUAL_TRYON_SERVICE_URL,
    TEXT2IMAGE_SERVICE_URL,
    ELEGANCE_SERVICE_URL,
    PPL_DETECTOR_SERVICE_URL,
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
@pytest.mark.timeout(300)  # Increase timeout to 5 minutes (300 seconds)
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
        
        # Check optional services
        try:
            tryon_health = await async_httpx_client.get(f"{VIRTUAL_TRYON_SERVICE_URL}/health", timeout=5.0)
            print(f"Virtual Try-on service health: {tryon_health.status_code}")
            has_tryon_service = tryon_health.status_code == 200
        except Exception:
            print("Virtual Try-on service is not available")
            has_tryon_service = False
            
        try:
            text2image_health = await async_httpx_client.get(f"{TEXT2IMAGE_SERVICE_URL}/health", timeout=5.0)
            print(f"Text2Image service health: {text2image_health.status_code}")
            has_text2image_service = text2image_health.status_code == 200
        except Exception:
            print("Text2Image service is not available")
            has_text2image_service = False
            
        try:
            elegance_health = await async_httpx_client.get(f"{ELEGANCE_SERVICE_URL}/health", timeout=5.0)
            print(f"Elegance service health: {elegance_health.status_code}")
            has_elegance_service = elegance_health.status_code == 200
        except Exception:
            print("Elegance service is not available")
            has_elegance_service = False
            
        try:
            ppl_detector_health = await async_httpx_client.get(f"{PPL_DETECTOR_SERVICE_URL}/health", timeout=5.0)
            print(f"People Detector service health: {ppl_detector_health.status_code}")
            has_ppl_detector_service = ppl_detector_health.status_code == 200
        except Exception:
            print("People Detector service is not available")
            has_ppl_detector_service = False
        
        print("All required services are healthy!")
    except Exception as e:
        pytest.skip(f"Required service health check failed: {str(e)}")
    
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
    if has_tryon_service:
        try:
            print("\n--- Step 4: Testing Virtual Try-On ---")
            
            # The virtual try-on service expects base64-encoded images in a JSON request
            # Convert images to base64 for the request
            model_image_b64 = base64.b64encode(person_image_data).decode('utf-8')
            garment_image_b64 = base64.b64encode(top_image_data).decode('utf-8')
            
            # Send a request using the format defined in the TryOnRequest Pydantic model
            try_on_request = {
                "model_image_data": model_image_b64,
                "garment_image_data": garment_image_b64,
                "category": "auto",
                "mode": "quality"
            }
            
            print("Sending try-on request to virtual try-on service...")
            print("Note: This step may take 1-2 minutes as it depends on an external AI service...")
            tryon_response = await async_httpx_client.post(
                f"{VIRTUAL_TRYON_SERVICE_URL}/tryon",
                json=try_on_request,
                timeout=120.0  # Virtual try-on can take longer
            )
            
            print(f"Try-on response status: {tryon_response.status_code}")
            
            if tryon_response.status_code == 200:
                try:
                    tryon_data = tryon_response.json()
                    
                    # The response should include base64-encoded result image
                    if "result_image_data" in tryon_data:
                        tryon_image_bytes = base64.b64decode(tryon_data["result_image_data"])
                        tryon_filename = f"e2e_tryon_{int(time.time())}.jpg"
                        save_test_image(tryon_image_bytes, tryon_filename)
                        print(f"Saved try-on result image: {tryon_filename}")
                    else:
                        print("No result_image_data in try-on response")
                    
                    # Display additional info from the response
                    if "details" in tryon_data:
                        details = tryon_data["details"]
                        print(f"Try-on details: status={details.get('status', 'unknown')}, "
                              f"category={details.get('category', 'unknown')}, "
                              f"mode={details.get('mode', 'unknown')}")
                except Exception as e:
                    print(f"Error processing try-on response: {str(e)}")
                    print(f"Response content: {tryon_response.text[:500]}")
            else:
                print(f"Try-on request failed with status {tryon_response.status_code}")
                print(f"Response content: {tryon_response.text[:500]}")
        except Exception as e:
            print(f"Virtual try-on test failed: {str(e)}")
    else:
        print("\n--- Skipping Virtual Try-On (service not available) ---")
    
    # Optional Step 7: Multi-garment Virtual Try-On (if available)
    if has_tryon_service:
        try:
            print("\n--- Step 5: Testing Multi-garment Virtual Try-On ---")
            
            # The multi-garment try-on service also expects base64-encoded images in a JSON request
            model_image_b64 = base64.b64encode(person_image_data).decode('utf-8')
            top_image_b64 = base64.b64encode(top_image_data).decode('utf-8')
            bottom_image_b64 = base64.b64encode(bottom_image_data).decode('utf-8')
            
            # Send a request using the format defined in the MultiTryOnRequest Pydantic model
            multi_tryon_request = {
                "model_image_data": model_image_b64,
                "top_image_data": top_image_b64,
                "bottom_image_data": bottom_image_b64,
                "mode": "quality"
            }
            
            print("Sending multi-garment try-on request...")
            print("Note: This step may take 2-5 minutes as it processes multiple garments through an external AI service...")
            multi_tryon_response = await async_httpx_client.post(
                f"{VIRTUAL_TRYON_SERVICE_URL}/tryon/multi",
                json=multi_tryon_request,
                timeout=240.0  # Multi-garment try-on can take even longer (4 minutes)
            )
            
            print(f"Multi-garment try-on response status: {multi_tryon_response.status_code}")
            
            if multi_tryon_response.status_code == 200:
                try:
                    multi_tryon_data = multi_tryon_response.json()
                    
                    # The response should include base64-encoded result image
                    if "final_result_data" in multi_tryon_data:
                        multi_tryon_image_bytes = base64.b64decode(multi_tryon_data["final_result_data"])
                        multi_tryon_filename = f"e2e_multi_tryon_{int(time.time())}.jpg"
                        save_test_image(multi_tryon_image_bytes, multi_tryon_filename)
                        print(f"Saved multi-garment try-on result image: {multi_tryon_filename}")
                    else:
                        print("No final_result_data in multi-garment try-on response")
                    
                    # Display additional info from the response
                    if "details" in multi_tryon_data:
                        details = multi_tryon_data["details"]
                        print(f"Multi-garment try-on details: status={details.get('status', 'unknown')}, "
                              f"top_processed={details.get('top_processed', False)}, "
                              f"bottom_processed={details.get('bottom_processed', False)}")
                except Exception as e:
                    print(f"Error processing multi-garment try-on response: {str(e)}")
                    print(f"Response content: {multi_tryon_response.text[:500]}")
            else:
                print(f"Multi-garment try-on request failed with status {multi_tryon_response.status_code}")
                print(f"Response content: {multi_tryon_response.text[:500]}")
        except Exception as e:
            print(f"Multi-garment virtual try-on test failed: {str(e)}")
    else:
        print("\n--- Skipping Multi-garment Virtual Try-On (service not available) ---")
    
    # Optional Step 8: Text-to-Image Generation (if available)
    if has_text2image_service:
        try:
            print("\n--- Step 6: Testing Text-to-Image Generation ---")
            
            # Fashion-related queries to test
            fashion_queries = [
                "a stylish casual outfit with blue jeans and white sneakers",
                "elegant black dress for formal occasions",
                "men's business suit with tie"
            ]
            
            # Select a random query
            selected_query = random.choice(fashion_queries)
            print(f"Using text-to-image query: '{selected_query}'")
            
            # Text-to-image request - use the correct endpoint and request format
            text2image_response = await async_httpx_client.post(
                f"{TEXT2IMAGE_SERVICE_URL}/text-search",
                json={"query": selected_query},
                timeout=120.0  # Image generation can take time
            )
            
            print(f"Text-to-image response status: {text2image_response.status_code}")
            
            if text2image_response.status_code == 200:
                # For successful requests, the response should be an image
                if "image/jpeg" in text2image_response.headers.get('content-type', ''):
                    # Save the image bytes directly
                    text2image_bytes = text2image_response.content
                    text2image_filename = f"e2e_text2image_{int(time.time())}.jpg"
                    save_test_image(text2image_bytes, text2image_filename)
                    print(f"Saved generated image: {text2image_filename}")
                else:
                    print(f"Unexpected text-to-image response format: {text2image_response.headers.get('content-type')}")
            else:
                print(f"Text-to-image request failed with status {text2image_response.status_code}")
                error_detail = text2image_response.json().get("detail", "No detail provided")
                print(f"Error detail: {error_detail}")
                
            # Also test the check-query endpoint, which validates if a query is clothing-related
            check_query_response = await async_httpx_client.post(
                f"{TEXT2IMAGE_SERVICE_URL}/check-query",
                json={"query": selected_query},
                timeout=30.0
            )
            
            print(f"Check query response status: {check_query_response.status_code}")
            
            if check_query_response.status_code == 200:
                check_data = check_query_response.json()
                is_clothing = check_data.get("is_clothing_related", False)
                message = check_data.get("message", "")
                print(f"Query is clothing-related: {is_clothing}")
                print(f"Message: {message}")
        except Exception as e:
            print(f"Text-to-image test failed: {str(e)}")
    else:
        print("\n--- Skipping Text-to-Image Generation (service not available) ---")
    
    # Optional Step 9: Elegance Chat (if available)
    if has_elegance_service:
        try:
            print("\n--- Step 7: Testing Elegance Chat ---")
            
            # Fashion-related chat message to test
            chat_messages = [
                "What should I wear to a summer wedding?",
                "How do I build a capsule wardrobe?",
                "Can you help me choose accessories for a black suit?"
            ]
            
            # Select a random message
            selected_message = random.choice(chat_messages)
            print(f"Using chat message: '{selected_message}'")
            
            # Chat request - use the correct API endpoint and request format
            chat_response = await async_httpx_client.post(
                f"{ELEGANCE_SERVICE_URL}/api/chat",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": selected_message
                        }
                    ],
                    "session_id": f"e2e_test_{int(time.time())}"
                },
                timeout=30.0
            )
            
            print(f"Chat response status: {chat_response.status_code}")
            
            if chat_response.status_code == 200:
                chat_data = chat_response.json()
                
                # Check if we have a response
                if "response" in chat_data:
                    print(f"Chat response (truncated): {chat_data['response'][:100]}...")
                    
                    # Verify the response has typical Elegance characteristics
                    has_french = any(word in chat_data['response'].lower() for word in ["chéri", "magnifique", "parfait", "voilà", "élégant"])
                    is_fashion_related = any(word in chat_data['response'].lower() for word in ["fashion", "style", "outfit", "wear", "dress", "clothing"])
                    
                    if has_french:
                        print("Response contains French expressions (as expected)")
                    
                    if is_fashion_related:
                        print("Response is fashion-related (as expected)")
                    
                    if "session_id" in chat_data:
                        print(f"Session ID: {chat_data['session_id']}")
                else:
                    print("No response in chat data")
            else:
                print(f"Chat request failed with status {chat_response.status_code}")
                try:
                    error_data = chat_response.json()
                    print(f"Error: {error_data}")
                except Exception:
                    print(f"Error content: {chat_response.text[:200]}")
        except Exception as e:
            print(f"Elegance chat test failed: {str(e)}")
    else:
        print("\n--- Skipping Elegance Chat (service not available) ---")
    
    # Optional Step 10: People Detection (if available)
    if has_ppl_detector_service:
        try:
            print("\n--- Step 8: Testing People Detection ---")
            
            # People detection request
            ppl_detect_files = {
                'file': ('person.jpg', person_image_data, 'image/jpeg')
            }
            
            # Count people
            count_response = await async_httpx_client.post(
                f"{PPL_DETECTOR_SERVICE_URL}/count_persons",
                files=ppl_detect_files,
                timeout=30.0
            )
            
            print(f"Count persons response status: {count_response.status_code}")
            
            if count_response.status_code == 200:
                count_data = count_response.json()
                
                # Check people count
                if "person_count" in count_data:
                    print(f"Detected {count_data['person_count']} people in the image")
                else:
                    print("No count in people detection response")
                
                # Get detections with bounding boxes
                detect_response = await async_httpx_client.post(
                    f"{PPL_DETECTOR_SERVICE_URL}/detect",
                    files=ppl_detect_files,
                    data={"include_crops": "True"},
                    timeout=30.0
                )
                
                print(f"Detect persons response status: {detect_response.status_code}")
                
                if detect_response.status_code == 200:
                    detect_data = detect_response.json()
                    
                    if "detections" in detect_data:
                        print(f"Got {len(detect_data['detections'])} person detections with bounding boxes")
                        
                        # Save person crops if available
                        for i, detection in enumerate(detect_data["detections"]):
                            if "crop_data" in detection and detection["crop_data"]:
                                try:
                                    crop_bytes = base64.b64decode(detection["crop_data"])
                                    crop_filename = f"e2e_person_crop_{i}_{int(time.time())}.jpg"
                                    save_test_image(crop_bytes, crop_filename)
                                    print(f"Saved person crop {i}: {crop_filename}")
                                except Exception as e:
                                    print(f"Could not save person crop {i}: {str(e)}")
                    else:
                        print("No detections in people detection response")
                else:
                    print(f"People detection request failed with status {detect_response.status_code}")
            else:
                print(f"People count request failed with status {count_response.status_code}")
        except Exception as e:
            print(f"People detection test failed: {str(e)}")
    else:
        print("\n--- Skipping People Detection (service not available) ---")
    
    print("\n=== End-to-End Fashion Advisor Test Completed Successfully ===") 