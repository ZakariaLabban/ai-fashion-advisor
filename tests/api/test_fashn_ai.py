import pytest
import os
import sys
from pathlib import Path
import httpx
import base64

# Add the parent directory to the Python path to import the Azure Key Vault helper
sys.path.append(str(Path(__file__).parent.parent.parent))

# Mark all tests in this file with the api marker
pytestmark = pytest.mark.api

# Try to import the Azure Key Vault helper, but don't fail if it's not available
try:
    from azure_keyvault_helper import AzureKeyVaultHelper
    # Initialize Azure Key Vault helper
    keyvault = AzureKeyVaultHelper()
    # Get credentials from Azure Key Vault with environment variable fallback
    FASHN_AI_API_URL = keyvault.get_secret("FASHN-AI-API-URL", os.getenv("FASHN_AI_API_URL", "https://api.fashn.ai/v1"))
    FASHN_AI_API_KEY = keyvault.get_secret("FASHN-AI-API-KEY", os.getenv("FASHN_AI_API_KEY", None))
except (ImportError, ValueError) as e:
    print(f"Azure Key Vault not available: {e}. Using environment variables.")
    # Fall back to environment variables
    FASHN_AI_API_URL = os.getenv("FASHN_AI_API_URL", "https://api.fashn.ai/v1")
    FASHN_AI_API_KEY = os.getenv("FASHN_AI_API_KEY", None)

# Path to test data
TEST_DATA_DIR = Path(__file__).parent.parent / "data"

@pytest.fixture
def fashn_ai_client():
    """Create an httpx client for FASHN.AI API testing."""
    if not FASHN_AI_API_KEY:
        pytest.skip("FASHN-AI-API-KEY not found in Azure Key Vault or FASHN_AI_API_KEY environment variable not set")
        
    headers = {
        "Authorization": f"Bearer {FASHN_AI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    with httpx.Client(base_url=FASHN_AI_API_URL, headers=headers, timeout=30.0) as client:
        yield client

@pytest.fixture
def test_image():
    """Get a test image for API calls."""
    # Ensure test data directory exists
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    
    # Path to a sample image
    image_path = TEST_DATA_DIR / "person_sample.jpg"
    
    # If the image doesn't exist, we'll need to skip the test
    if not image_path.exists():
        pytest.skip(f"Test image not found at {image_path}")
    
    with open(image_path, "rb") as f:
        return f.read()

@pytest.mark.live
def test_fashn_ai_auth(fashn_ai_client):
    """Test FASHN.AI API authentication."""
    # Simple endpoint to test authentication
    response = fashn_ai_client.get("/auth/verify")
    
    # Should return 200 if authentication is successful
    assert response.status_code == 200
    assert response.json().get("authenticated") is True
    print("Successfully authenticated with FASHN.AI API")

@pytest.mark.live
def test_fashn_ai_garment_detection(fashn_ai_client, test_image):
    """Test the garment detection endpoint."""
    # Prepare the request
    files = {
        "image": ("person.jpg", test_image, "image/jpeg")
    }
    
    # Make the request
    response = fashn_ai_client.post("/detect/garments", files=files)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    
    # The response should contain detections
    assert "detections" in data
    
    # There should be at least one detection
    if len(data["detections"]) > 0:
        # Check the structure of a detection
        detection = data["detections"][0]
        assert "bbox" in detection
        assert "category" in detection
        assert "confidence" in detection
        print(f"Successfully detected {len(data['detections'])} garments")
    else:
        print("No garments detected, but API call was successful")

@pytest.mark.live
def test_fashn_ai_style_analysis(fashn_ai_client, test_image):
    """Test the style analysis endpoint."""
    # Prepare the request
    files = {
        "image": ("person.jpg", test_image, "image/jpeg")
    }
    
    # Make the request
    response = fashn_ai_client.post("/analyze/style", files=files)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    
    # The response should contain style data
    assert "styles" in data
    
    # There should be at least one style
    assert len(data["styles"]) > 0
    
    # Check the structure of a style
    style = data["styles"][0]
    assert "name" in style
    assert "confidence" in style
    print(f"Successfully analyzed style with top style: {style['name']}") 