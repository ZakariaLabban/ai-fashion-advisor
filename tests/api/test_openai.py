import pytest
import os
import sys
from pathlib import Path
import httpx
import time
from openai import OpenAI

# Add the parent directory to the Python path to import the Azure Key Vault helper
sys.path.append(str(Path(__file__).parent.parent.parent))
from azure_keyvault_helper import AzureKeyVaultHelper

# Mark all tests in this file with the api marker
pytestmark = pytest.mark.api

# Initialize Azure Key Vault helper
keyvault = AzureKeyVaultHelper()

# Get credentials from Azure Key Vault with environment variable fallback
OPENAI_API_KEY = keyvault.get_secret("OPENAI-API-KEY", os.getenv("OPENAI_API_KEY", None))

@pytest.fixture
def openai_client():
    """Create an OpenAI client for testing."""
    if not OPENAI_API_KEY:
        pytest.skip("OPENAI-API-KEY secret not found in Azure Key Vault or OPENAI_API_KEY environment variable not set")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    return client

@pytest.mark.live
def test_openai_connection(openai_client):
    """Test the connection to OpenAI API by listing models."""
    models = openai_client.models.list()
    
    # If we can get models, the connection is working
    assert models is not None
    assert len(models.data) > 0
    print(f"Successfully connected to OpenAI API. Available models: {len(models.data)}")

@pytest.mark.live
def test_openai_completion(openai_client):
    """Test the completion API."""
    # Create a simple completion request
    completion = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a fashion advisor assistant."},
            {"role": "user", "content": "Suggest a business casual outfit for a man."}
        ],
        max_tokens=150
    )
    
    # Assertions
    assert completion is not None
    assert completion.choices is not None
    assert len(completion.choices) > 0
    assert completion.choices[0].message.content is not None
    assert len(completion.choices[0].message.content) > 0
    print(f"Got completion response with {len(completion.choices[0].message.content)} characters")

@pytest.mark.live
def test_openai_embedding(openai_client):
    """Test the embedding API."""
    # Create an embedding request
    embedding = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input="A blue denim jacket with white t-shirt"
    )
    
    # Assertions
    assert embedding is not None
    assert embedding.data is not None
    assert len(embedding.data) > 0
    assert embedding.data[0].embedding is not None
    assert len(embedding.data[0].embedding) > 0
    print(f"Got embedding vector with {len(embedding.data[0].embedding)} dimensions")

@pytest.mark.live
def test_openai_image_generation(openai_client):
    """Test the image generation API."""
    # Generate an image
    response = openai_client.images.generate(
        model="dall-e-3",
        prompt="A professional fashion photo of a business casual outfit for men, on white background",
        n=1,
        size="1024x1024"
    )
    
    # Assertions
    assert response is not None
    assert response.data is not None
    assert len(response.data) > 0
    assert response.data[0].url is not None
    assert response.data[0].url.startswith("https://")
    print(f"Successfully generated image: {response.data[0].url}")

@pytest.mark.live
def test_openai_vision(openai_client):
    """Test the vision API with a simple prompt."""
    # This test requires an image URL
    # For test purposes, we'll use a publicly available image
    image_url = "https://plus.unsplash.com/premium_photo-1661355543486-39310d963a4a?w=800&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTd8fGZhc2hpb24lMjBvdXRmaXR8ZW58MHx8MHx8fDA%3D"
    
    # Create a vision request
    response = openai_client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": "Describe this outfit in detail. What style is it?"},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        max_tokens=300
    )
    
    # Assertions
    assert response is not None
    assert response.choices is not None
    assert len(response.choices) > 0
    assert response.choices[0].message.content is not None
    assert len(response.choices[0].message.content) > 0
    print(f"Got vision API response with {len(response.choices[0].message.content)} characters") 