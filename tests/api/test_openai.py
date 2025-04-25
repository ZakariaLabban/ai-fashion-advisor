import pytest
import os
import sys
from pathlib import Path
import time
from openai import OpenAI

# Add the parent directory to the Python path to import the Azure Key Vault helper
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import helper to read from docker-compose.yml
from tests.api.docker_env_reader import setup_azure_keyvault

# Mark all tests in this file with the api marker
pytestmark = pytest.mark.api

# Initialize variables with None to handle case where Azure Key Vault is not available
OPENAI_API_KEY = None

# Setup Azure Key Vault URL from environment or docker-compose.yml
setup_azure_keyvault()

# Try to get credentials from Azure Key Vault
try:
    from azure_keyvault_helper import AzureKeyVaultHelper
    # Initialize Azure Key Vault helper
    keyvault = AzureKeyVaultHelper()
    # Get credentials from Azure Key Vault
    OPENAI_API_KEY = keyvault.get_secret("OPENAI-API-KEY")
    
    print("Successfully retrieved OpenAI API key from Azure Key Vault")
except (ImportError, ValueError) as e:
    print(f"Azure Key Vault not available: {e}")

# Only fall back to environment variables if Azure Key Vault didn't provide values
if not OPENAI_API_KEY:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        print("Using OPENAI_API_KEY from environment variable")

@pytest.fixture
def openai_client():
    """Create an OpenAI client for testing."""
    if not OPENAI_API_KEY:
        pytest.skip("OPENAI-API-KEY not found in Azure Key Vault or OPENAI_API_KEY environment variable not set")
    
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
def test_openai_text_completion(openai_client):
    """Test the text completion API."""
    # Create a simple completion request with fashion-related input
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
    print(f"Got text completion response with {len(completion.choices[0].message.content)} characters") 