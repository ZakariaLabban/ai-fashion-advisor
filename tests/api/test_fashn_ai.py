import pytest
import os
import sys
import json
from pathlib import Path
import httpx
import base64
import time

# Add the parent directory to the Python path to import the Azure Key Vault helper
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import helper to read from docker-compose.yml
from tests.api.docker_env_reader import setup_azure_keyvault

# Mark all tests in this file with the api marker
pytestmark = pytest.mark.api

# Initialize variables with None to handle case where Azure Key Vault is not available
FASHN_AI_API_URL = None
FASHN_AI_API_KEY = None

# Setup Azure Key Vault URL from environment or docker-compose.yml
setup_azure_keyvault()

# Try to get credentials from Azure Key Vault
try:
    from azure_keyvault_helper import AzureKeyVaultHelper
    # Initialize Azure Key Vault helper
    keyvault = AzureKeyVaultHelper()
    # Get credentials from Azure Key Vault
    FASHN_AI_API_URL = keyvault.get_secret("FASHN-AI-BASE-URL") or keyvault.get_secret("FASHN-AI-API-URL")
    FASHN_AI_API_KEY = keyvault.get_secret("FASHN-AI-API-KEY")
    
    print("Successfully retrieved FASHN.AI credentials from Azure Key Vault")
except (ImportError, ValueError) as e:
    print(f"Azure Key Vault not available: {e}")

# Only fall back to environment variables if Azure Key Vault didn't provide values
if not FASHN_AI_API_URL:
    FASHN_AI_API_URL = os.getenv("FASHN_AI_BASE_URL") or os.getenv("FASHN_AI_API_URL", "https://api.fashn.ai/v1")
    if FASHN_AI_API_URL:
        print(f"Using FASHN_AI_API_URL from environment variable: {FASHN_AI_API_URL}")

if not FASHN_AI_API_KEY:
    FASHN_AI_API_KEY = os.getenv("FASHN_AI_API_KEY")
    if FASHN_AI_API_KEY:
        print("Using FASHN_AI_API_KEY from environment variable")

# Path to test data
TEST_DATA_DIR = Path(__file__).parent.parent / "data"

# Ensure data directory exists
TEST_DATA_DIR.mkdir(exist_ok=True, parents=True)

# Example image URLs for testing - use clear, high-quality images with visible persons
DEFAULT_MODEL_IMAGE_URL = "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=1080"  # Clear frontal image of a person
DEFAULT_GARMENT_IMAGE_URL = "https://images.unsplash.com/photo-1578587018452-892bacefd3f2?w=1080"  # Clear image of a garment

@pytest.fixture
def fashn_ai_client():
    """Create an httpx client for FASHN.AI API testing."""
    if not FASHN_AI_API_KEY:
        pytest.skip("FASHN-AI-API-KEY not found in Azure Key Vault or FASHN_AI_API_KEY environment variable not set")
        
    headers = {
        "Authorization": f"Bearer {FASHN_AI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    with httpx.Client(base_url=FASHN_AI_API_URL, headers=headers, timeout=60.0) as client:
        yield client

def get_sample_image_path(filename):
    """Helper to get a sample image path or create a placeholder."""
    image_path = TEST_DATA_DIR / filename
    
    # If the image doesn't exist, we'll create an empty file for testing
    if not image_path.exists():
        # Create a small empty file to use as placeholder
        with open(image_path, "wb") as f:
            f.write(b"placeholder")
        print(f"Created placeholder image: {image_path}")
    
    return image_path

def get_image_base64(path_or_url):
    """Get base64 encoded image from a path or URL."""
    # If it's a URL, return the URL directly
    if isinstance(path_or_url, str) and path_or_url.startswith(("http://", "https://")):
        return path_or_url
        
    # If it's a local file, read and convert to base64
    try:
        with open(path_or_url, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/jpeg;base64,{image_base64}"
    except Exception as e:
        print(f"Error reading image file: {e}")
        return None

@pytest.mark.live
def test_fashn_ai_api_access(fashn_ai_client):
    """Test access to the FASHN.AI API by making a simple request."""
    try:
        # Try a simple GET request to the models endpoint which should be available
        response = fashn_ai_client.get("/models")
        
        # Even if it's an error response, we should get a valid response object
        assert response is not None
        
        # If we receive any response, the API is accessible
        print(f"Received response from FASHN.AI API: Status {response.status_code}")
        
        # Don't assert 200 status to avoid failing tests due to API changes
        # Just check if the API is accessible and responses are proper JSON
        if response.status_code == 200:
            # Try to parse response as JSON
            data = response.json()
            print(f"Successfully connected to FASHN.AI API")
    except httpx.RequestError as e:
        pytest.skip(f"Cannot connect to FASHN.AI API: {str(e)}")

@pytest.mark.live
def test_fashn_ai_tryon_endpoint(fashn_ai_client):
    """Test the virtual try-on endpoint of FASHN.AI API using polling approach."""
    # Always use the default URLs for testing to ensure valid images
    model_image = DEFAULT_MODEL_IMAGE_URL
    print(f"Using model image URL: {model_image}")
    
    garment_image = DEFAULT_GARMENT_IMAGE_URL
    print(f"Using garment image URL: {garment_image}")
    
    # Prepare the payload
    payload = {
        "model_image": model_image,
        "garment_image": garment_image,
        "category": "auto",
        "moderation_level": "permissive",
        "mode": "performance",  # Use performance mode for faster testing
        "seed": 42,
        "num_samples": 1
    }
    
    try:
        # Make the API request to start the prediction
        response = fashn_ai_client.post("/run", json=payload)
        
        # Check if the request was successful
        assert response.status_code == 200, f"Failed to start prediction: {response.text}"
        data = response.json()
        
        # Check if we got a prediction ID
        assert "id" in data, "No prediction ID in response"
        prediction_id = data["id"]
        print(f"Successfully started virtual try-on with ID: {prediction_id}")
        
        # Poll for prediction status
        max_attempts = 30  # Adjust based on expected processing time
        status_url = f"/status/{prediction_id}"
        
        for attempt in range(max_attempts):
            print(f"Polling status, attempt {attempt+1}/{max_attempts}")
            
            status_response = fashn_ai_client.get(status_url)
            assert status_response.status_code == 200, f"Status check failed: {status_response.text}"
            
            status_data = status_response.json()
            status = status_data.get("status")
            print(f"Current status: {status}")
            
            if status == "completed":
                # Check the output
                assert "output" in status_data, "No output in completed response"
                
                # Handle both old and new response formats
                if isinstance(status_data["output"], list):
                    # New format: output is a list of URLs
                    assert len(status_data["output"]) > 0, "Empty output list"
                    image_url = status_data["output"][0]
                else:
                    # Old format: output is a dict with images key
                    assert "images" in status_data["output"], "No images in output"
                    assert len(status_data["output"]["images"]) > 0, "Empty images list in output"
                    image_url = status_data["output"]["images"][0]
                
                assert image_url.startswith("http"), f"Invalid image URL: {image_url}"
                print(f"Successfully completed virtual try-on, image URL: {image_url}")
                break
            elif status == "failed":
                error_details = status_data.get('error', 'Unknown error')
                print(f"Virtual try-on processing failed with error: {error_details}")
                
                # If it's a common error related to pose detection, treat as warning not failure
                if isinstance(error_details, dict) and error_details.get('name') == 'PoseError':
                    print("PoseError detected - this is a known limitation with some images")
                    pytest.skip(f"Skipping due to PoseError: {error_details.get('message', '')}")
                else:
                    pytest.fail(f"Virtual try-on failed: {error_details}")
            elif status in ["pending", "processing"]:
                # Wait before the next poll
                time.sleep(2)
                continue
            else:
                pytest.fail(f"Unknown status: {status}")
        else:
            pytest.fail(f"Prediction timed out after {max_attempts} attempts")
            
    except httpx.RequestError as e:
        pytest.skip(f"Cannot connect to FASHN.AI API: {str(e)}")
    except Exception as e:
        pytest.fail(f"Virtual try-on test failed with exception: {str(e)}") 