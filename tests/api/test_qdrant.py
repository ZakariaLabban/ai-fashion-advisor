import pytest
import os
import sys
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

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
    QDRANT_URL = keyvault.get_secret("QDRANT-URL", os.getenv("QDRANT_URL", "http://localhost:6333"))
    QDRANT_API_KEY = keyvault.get_secret("QDRANT-API-KEY", os.getenv("QDRANT_API_KEY", None))
except (ImportError, ValueError) as e:
    print(f"Azure Key Vault not available: {e}. Using environment variables.")
    # Fall back to environment variables
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)

@pytest.fixture
def qdrant_client():
    """Create a Qdrant client for testing."""
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return client

@pytest.mark.live
def test_qdrant_connection(qdrant_client):
    """Test the connection to Qdrant."""
    # Get cluster info as a basic test
    cluster_info = qdrant_client.get_cluster_info()
    
    # If we can get cluster info, the connection is working
    assert cluster_info is not None
    print(f"Connected to Qdrant cluster: {cluster_info}")

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