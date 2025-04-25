import pytest
import os
import sys
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.http.exceptions import ResponseHandlingException

# Add the parent directory to the Python path to import the Azure Key Vault helper
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import helper to read from docker-compose.yml
from tests.api.docker_env_reader import setup_azure_keyvault

# Mark all tests in this file with the api marker
pytestmark = pytest.mark.api

# Initialize variables with None to handle case where Azure Key Vault is not available
QDRANT_URL = None
QDRANT_API_KEY = None

# Setup Azure Key Vault URL from environment or docker-compose.yml
setup_azure_keyvault()

# Try to get credentials from Azure Key Vault
try:
    from azure_keyvault_helper import AzureKeyVaultHelper
    # Initialize Azure Key Vault helper
    keyvault = AzureKeyVaultHelper()
    # Get credentials from Azure Key Vault
    QDRANT_URL = keyvault.get_secret("QDRANT-URL")
    QDRANT_API_KEY = keyvault.get_secret("QDRANT-API-KEY")
    
    print("Successfully retrieved Qdrant Cloud credentials from Azure Key Vault")
except (ImportError, ValueError) as e:
    print(f"Azure Key Vault not available: {e}")

# Only fall back to environment variables if Azure Key Vault didn't provide values
if not QDRANT_URL:
    QDRANT_URL = os.getenv("QDRANT_URL")
    if QDRANT_URL:
        print("Using QDRANT_URL from environment variable")

if not QDRANT_API_KEY:
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    if QDRANT_API_KEY:
        print("Using QDRANT_API_KEY from environment variable")

@pytest.fixture
def qdrant_client():
    """Create a Qdrant client for testing."""
    # Skip if URL or API key is not provided from either Azure Key Vault or environment variables
    if not QDRANT_URL:
        pytest.skip("QDRANT-URL not found in Azure Key Vault or QDRANT_URL environment variable not set")
    
    if not QDRANT_API_KEY:
        pytest.skip("QDRANT-API-KEY not found in Azure Key Vault or QDRANT_API_KEY environment variable not set")
        
    # Create the client with timeout to avoid long waits if connection fails
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=10.0)
    
    # Check if Qdrant is available by making a simple API call
    try:
        # Use get_collections() to test connection
        client.get_collections()
    except ResponseHandlingException as e:
        pytest.skip(f"Cannot connect to Qdrant Cloud: {e}")
    except Exception as e:
        pytest.skip(f"Unexpected error connecting to Qdrant Cloud: {e}")
    
    return client

@pytest.mark.live
def test_qdrant_connection(qdrant_client):
    """Test the connection to Qdrant."""
    # Get collections as a basic test
    collections = qdrant_client.get_collections()
    
    # If we can get collections, the connection is working
    assert collections is not None
    print(f"Connected to Qdrant Cloud. Available collections: {collections}")

@pytest.mark.live
def test_qdrant_basic_operations(qdrant_client):
    """Test basic vector operations in Qdrant."""
    # Collection name for testing
    test_collection_name = "test_fashion_vectors"
    
    # Check if the collection exists and recreate it
    collections = qdrant_client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    if test_collection_name in collection_names:
        qdrant_client.delete_collection(collection_name=test_collection_name)
    
    # Create a test collection
    qdrant_client.create_collection(
        collection_name=test_collection_name,
        vectors_config=VectorParams(size=4, distance=Distance.COSINE),
    )
    
    # Insert some test vectors
    qdrant_client.upsert(
        collection_name=test_collection_name,
        points=[
            {
                "id": 1, 
                "vector": [0.1, 0.2, 0.3, 0.4],
                "payload": {"style": "casual", "color": "blue"}
            },
            {
                "id": 2, 
                "vector": [0.2, 0.3, 0.4, 0.5],
                "payload": {"style": "formal", "color": "black"}
            }
        ]
    )
    
    # Search for similar vectors
    search_results = qdrant_client.search(
        collection_name=test_collection_name,
        query_vector=[0.1, 0.2, 0.3, 0.4],
        limit=1
    )
    
    # Clean up
    qdrant_client.delete_collection(collection_name=test_collection_name)
    
    # Assertions
    assert len(search_results) == 1
    assert search_results[0].id == 1
    assert search_results[0].payload["style"] == "casual" 