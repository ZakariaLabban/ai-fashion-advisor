import os
import pytest
import base64
import json
from pathlib import Path
import httpx
from PIL import Image
import numpy as np
import io

# Set base URLs for services (use environment variables for flexibility)
DETECTION_SERVICE_URL = os.getenv("DETECTION_SERVICE_URL", "http://localhost:7001")
STYLE_SERVICE_URL = os.getenv("STYLE_SERVICE_URL", "http://localhost:7002")
FEATURE_SERVICE_URL = os.getenv("FEATURE_SERVICE_URL", "http://localhost:7003")
VIRTUAL_TRYON_SERVICE_URL = os.getenv("VIRTUAL_TRYON_SERVICE_URL", "http://localhost:7004")
ELEGANCE_SERVICE_URL = os.getenv("ELEGANCE_SERVICE_URL", "http://localhost:7005")
RECO_DATA_SERVICE_URL = os.getenv("RECO_DATA_SERVICE_URL", "http://localhost:7007")
MATCH_SERVICE_URL = os.getenv("MATCH_SERVICE_URL", "http://localhost:7008")
TEXT2IMAGE_SERVICE_URL = os.getenv("TEXT2IMAGE_SERVICE_URL", "http://localhost:7020")
PPL_DETECTOR_SERVICE_URL = os.getenv("PPL_DETECTOR_SERVICE_URL", "http://localhost:7009")
EEP_SERVICE_URL = os.getenv("EEP_SERVICE_URL", "http://localhost:7000")

# Path to test data
TEST_DATA_DIR = Path(__file__).parent / "data"

@pytest.fixture
def create_test_data_dir():
    """Ensure test data directory exists."""
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    return TEST_DATA_DIR

@pytest.fixture
def httpx_client():
    """Create an httpx client for testing."""
    with httpx.Client(timeout=60.0) as client:
        yield client

@pytest.fixture
def async_httpx_client():
    """Create an async httpx client for testing."""
    return httpx.AsyncClient(timeout=60.0)

@pytest.fixture
def mock_image_file():
    """Create a mock image file for testing."""
    # Create a simple 100x100 RGB image
    img = Image.new('RGB', (100, 100), color=(73, 109, 137))
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    return img_io.getvalue()

@pytest.fixture
def sample_tshirt_image(create_test_data_dir):
    """Create or return a sample t-shirt image for testing."""
    tshirt_path = TEST_DATA_DIR / "tshirt_sample.jpg"
    
    # If we don't have a sample image yet, create a simple one
    if not tshirt_path.exists():
        # Create a simple t-shirt shaped image
        img = Image.new('RGB', (300, 400), color=(255, 255, 255))
        # Draw a simple t-shirt shape (just for testing)
        img_array = np.array(img)
        
        # Draw sleeves
        for x in range(50, 250):
            for y in range(100, 150):
                if ((x - 50) ** 2 + (y - 100) ** 2 <= 2500 or 
                    (x - 250) ** 2 + (y - 100) ** 2 <= 2500):
                    img_array[y, x] = (30, 144, 255)  # Blue

        # Draw body
        for x in range(100, 200):
            for y in range(100, 350):
                img_array[y, x] = (30, 144, 255)  # Blue
                
        img = Image.fromarray(img_array)
        img.save(tshirt_path)
    
    with open(tshirt_path, 'rb') as f:
        return f.read()

@pytest.fixture
def sample_pants_image(create_test_data_dir):
    """Create or return a sample pants image for testing."""
    pants_path = TEST_DATA_DIR / "pants_sample.jpg"
    
    # If we don't have a sample image yet, create a simple one
    if not pants_path.exists():
        # Create a simple pants shaped image
        img = Image.new('RGB', (300, 500), color=(255, 255, 255))
        # Draw a simple pants shape (just for testing)
        img_array = np.array(img)
        
        # Draw pants
        for x in range(100, 200):
            for y in range(100, 450):
                img_array[y, x] = (0, 0, 0)  # Black
                
        # Draw legs
        for x in range(80, 120):
            for y in range(250, 450):
                img_array[y, x] = (0, 0, 0)  # Black
                
        for x in range(180, 220):
            for y in range(250, 450):
                img_array[y, x] = (0, 0, 0)  # Black
                
        img = Image.fromarray(img_array)
        img.save(pants_path)
    
    with open(pants_path, 'rb') as f:
        return f.read()

@pytest.fixture
def sample_person_image(create_test_data_dir):
    """Create or return a sample person image for testing."""
    person_path = TEST_DATA_DIR / "person_sample.jpg"
    
    # If we don't have a sample image yet, create a simple one
    if not person_path.exists():
        # Create a simple person shaped image
        img = Image.new('RGB', (300, 600), color=(255, 255, 255))
        # Draw a simple person shape (just for testing)
        img_array = np.array(img)
        
        # Draw head
        for x in range(125, 175):
            for y in range(50, 100):
                if (x - 150) ** 2 + (y - 75) ** 2 <= 625:
                    img_array[y, x] = (255, 226, 198)  # Skin tone
                    
        # Draw body
        for x in range(125, 175):
            for y in range(100, 350):
                img_array[y, x] = (255, 0, 0)  # Red shirt
                
        # Draw legs
        for x in range(125, 145):
            for y in range(350, 550):
                img_array[y, x] = (0, 0, 255)  # Blue pants
                
        for x in range(155, 175):
            for y in range(350, 550):
                img_array[y, x] = (0, 0, 255)  # Blue pants
                
        # Draw arms
        for x in range(75, 125):
            for y in range(150, 170):
                img_array[y, x] = (255, 0, 0)  # Red shirt
                
        for x in range(175, 225):
            for y in range(150, 170):
                img_array[y, x] = (255, 0, 0)  # Red shirt
                
        img = Image.fromarray(img_array)
        img.save(person_path)
    
    with open(person_path, 'rb') as f:
        return f.read()

@pytest.fixture
def sample_multiple_people_image(create_test_data_dir):
    """Create or return a sample image with multiple people for testing."""
    people_path = TEST_DATA_DIR / "multiple_people_sample.jpg"
    
    # If we don't have a sample image yet, create a simple one
    if not people_path.exists():
        # Create an image with 2 simple person shapes
        img = Image.new('RGB', (600, 600), color=(255, 255, 255))
        img_array = np.array(img)
        
        # Person 1
        # Draw head
        for x in range(125, 175):
            for y in range(50, 100):
                if (x - 150) ** 2 + (y - 75) ** 2 <= 625:
                    img_array[y, x] = (255, 226, 198)  # Skin tone
                    
        # Draw body
        for x in range(125, 175):
            for y in range(100, 350):
                img_array[y, x] = (255, 0, 0)  # Red shirt
                
        # Draw legs
        for x in range(125, 145):
            for y in range(350, 550):
                img_array[y, x] = (0, 0, 255)  # Blue pants
                
        for x in range(155, 175):
            for y in range(350, 550):
                img_array[y, x] = (0, 0, 255)  # Blue pants
        
        # Person 2
        # Draw head
        for x in range(425, 475):
            for y in range(50, 100):
                if (x - 450) ** 2 + (y - 75) ** 2 <= 625:
                    img_array[y, x] = (255, 226, 198)  # Skin tone
                    
        # Draw body
        for x in range(425, 475):
            for y in range(100, 350):
                img_array[y, x] = (0, 128, 0)  # Green shirt
                
        # Draw legs
        for x in range(425, 445):
            for y in range(350, 550):
                img_array[y, x] = (139, 69, 19)  # Brown pants
                
        for x in range(455, 475):
            for y in range(350, 550):
                img_array[y, x] = (139, 69, 19)  # Brown pants
                
        img = Image.fromarray(img_array)
        img.save(people_path)
    
    with open(people_path, 'rb') as f:
        return f.read()

@pytest.fixture
def sample_formal_clothing_image(create_test_data_dir):
    """Create or return a sample formal clothing image for testing."""
    formal_path = TEST_DATA_DIR / "formal_sample.jpg"
    
    # If we don't have a sample image yet, create a simple one
    if not formal_path.exists():
        # Create a simple formal clothing image
        img = Image.new('RGB', (300, 600), color=(255, 255, 255))
        img_array = np.array(img)
        
        # Draw a suit jacket
        for x in range(100, 200):
            for y in range(100, 350):
                img_array[y, x] = (0, 0, 0)  # Black
                
        # Draw a white shirt
        for x in range(130, 170):
            for y in range(120, 330):
                img_array[y, x] = (255, 255, 255)  # White
                
        # Draw a tie
        for x in range(145, 155):
            for y in range(150, 300):
                img_array[y, x] = (128, 0, 0)  # Maroon
                
        img = Image.fromarray(img_array)
        img.save(formal_path)
    
    with open(formal_path, 'rb') as f:
        return f.read()

@pytest.fixture
def sample_casual_clothing_image(create_test_data_dir):
    """Create or return a sample casual clothing image for testing."""
    casual_path = TEST_DATA_DIR / "casual_sample.jpg"
    
    # If we don't have a sample image yet, create a simple one
    if not casual_path.exists():
        # Create a simple casual clothing image
        img = Image.new('RGB', (300, 400), color=(255, 255, 255))
        img_array = np.array(img)
        
        # Draw a t-shirt
        for x in range(100, 200):
            for y in range(100, 300):
                img_array[y, x] = (50, 205, 50)  # Lime Green
                
        # Draw sleeves
        for x in range(50, 100):
            for y in range(100, 150):
                img_array[y, x] = (50, 205, 50)  # Lime Green
                
        for x in range(200, 250):
            for y in range(100, 150):
                img_array[y, x] = (50, 205, 50)  # Lime Green
                
        # Draw design
        for x in range(130, 170):
            for y in range(150, 190):
                img_array[y, x] = (255, 255, 0)  # Yellow
                
        img = Image.fromarray(img_array)
        img.save(casual_path)
    
    with open(casual_path, 'rb') as f:
        return f.read()

def encode_image_base64(image_bytes):
    """Encode image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode('utf-8')

@pytest.fixture
def valid_detection_response():
    """Return a valid detection response for mocking."""
    return {
        "detections": [
            {
                "class_name": "Shirt",
                "class_id": 4,
                "confidence": 0.92,
                "bbox": [50, 100, 250, 350],
                "crop_data": "base64_encoded_data_placeholder"
            },
            {
                "class_name": "Pants",
                "class_id": 10,
                "confidence": 0.88,
                "bbox": [75, 360, 225, 580],
                "crop_data": "base64_encoded_data_placeholder"
            }
        ],
        "processing_time": 0.45,
        "image_size": [600, 800]
    }

@pytest.fixture
def valid_style_response():
    """Return a valid style response for mocking."""
    return {
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
        "processing_time": 0.32
    }

@pytest.fixture
def valid_feature_response():
    """Return a valid feature response for mocking."""
    return {
        "features": [0.12, 0.34, 0.56, 0.78, 0.90, -0.12, -0.34, -0.56],
        "color_histogram": [0.05, 0.15, 0.25, 0.20, 0.10, 0.25],
        "processing_time": 0.28
    }

@pytest.fixture
def valid_match_response():
    """Return a valid match response for mocking."""
    return {
        "match_score": 78,
        "analysis": {
            "color_harmony": {
                "score": 85,
                "analysis": "These colors work well together. The blue top complements the black bottom."
            },
            "style_consistency": {
                "score": 70,
                "analysis": "The casual top and bottom create a cohesive look."
            },
            "occasion_appropriateness": {
                "score": 80,
                "analysis": "This outfit is appropriate for casual everyday wear."
            },
            "feature_match": {
                "score": 75,
                "analysis": "The features of these items indicate good compatibility."
            },
            "color_histogram_match": {
                "score": 80,
                "analysis": "The color distribution between these items is harmonious."
            }
        },
        "suggestions": [
            "Consider adding a light jacket to complete this look.",
            "Accessorize with a simple necklace for added interest.",
            "Neutral shoes would pair well with this outfit."
        ]
    } 