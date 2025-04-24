import os
import tempfile
import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureBlobHelper:
    """
    Helper class to download models from Azure Blob Storage.
    This class provides a centralized way to access models for all services.
    """
    _instance = None
    _client = None
    _downloaded_models = {}  # Track downloaded model paths

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AzureBlobHelper, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the Azure Blob Storage client"""
        # Get Blob Storage connection string or account name from environment
        connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        account_url = os.environ.get("AZURE_STORAGE_ACCOUNT_URL")
        
        try:
            if connection_string:
                logger.info("Initializing Azure Blob Storage client with connection string")
                self._client = BlobServiceClient.from_connection_string(connection_string)
            elif account_url:
                logger.info(f"Initializing Azure Blob Storage client with account URL: {account_url}")
                credential = DefaultAzureCredential()
                self._client = BlobServiceClient(account_url=account_url, credential=credential)
            else:
                logger.error("Neither AZURE_STORAGE_CONNECTION_STRING nor AZURE_STORAGE_ACCOUNT_URL is set")
                raise ValueError("Either AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_URL must be set")
                
            logger.info("Successfully initialized Azure Blob Storage client")
        except Exception as e:
            logger.error(f"Error initializing Azure Blob Storage client: {str(e)}")
            raise
        
    def download_model(self, container_name, blob_name, local_path=None, check_md5=True):
        """
        Download a model from Azure Blob Storage
        
        Args:
            container_name: Name of the container (e.g., 'models')
            blob_name: Name of the blob/model file (e.g., 'yolov8_style_model.pt')
            local_path: Local path to save the model file to. If None, saves to a temporary file.
            check_md5: Whether to check if the local file's MD5 matches the blob's MD5
            
        Returns:
            Path to the downloaded model file
        """
        key = f"{container_name}/{blob_name}"
        
        # If model is already downloaded and check_md5 is False, return cached path
        if key in self._downloaded_models and not check_md5:
            logger.info(f"Using previously downloaded model for {key}")
            return self._downloaded_models[key]
            
        # Create the container client
        try:
            container_client = self._client.get_container_client(container_name)
        except Exception as e:
            logger.error(f"Error getting container '{container_name}': {str(e)}")
            raise
            
        # Create the blob client
        try:
            blob_client = container_client.get_blob_client(blob_name)
        except Exception as e:
            logger.error(f"Error getting blob '{blob_name}': {str(e)}")
            raise
            
        # Check if the blob exists
        if not blob_client.exists():
            logger.error(f"Blob '{blob_name}' does not exist in container '{container_name}'")
            raise FileNotFoundError(f"Blob '{blob_name}' does not exist in container '{container_name}'")
            
        # Determine the local path
        if local_path is None:
            # Create a temporary file with the same extension as the blob
            _, ext = os.path.splitext(blob_name)
            fd, temp_path = tempfile.mkstemp(suffix=ext)
            os.close(fd)  # Close the file descriptor
            local_path = temp_path
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
            
        # Download the blob
        try:
            logger.info(f"Downloading '{blob_name}' from '{container_name}' to '{local_path}'")
            with open(local_path, "wb") as f:
                blob_data = blob_client.download_blob()
                blob_data.readinto(f)
                
            # Cache the local path
            self._downloaded_models[key] = local_path
            
            logger.info(f"Successfully downloaded '{blob_name}' to '{local_path}'")
            return local_path
        except Exception as e:
            logger.error(f"Error downloading '{blob_name}': {str(e)}")
            raise
            
    def get_model_properties(self, container_name, blob_name):
        """
        Get properties of a model blob
        
        Args:
            container_name: Name of the container (e.g., 'models')
            blob_name: Name of the blob/model file (e.g., 'yolov8_style_model.pt')
            
        Returns:
            Dictionary of blob properties
        """
        try:
            container_client = self._client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            properties = blob_client.get_blob_properties()
            return {
                "name": blob_name,
                "size": properties.size,
                "content_md5": properties.content_settings.content_md5,
                "last_modified": properties.last_modified,
                "etag": properties.etag
            }
        except Exception as e:
            logger.error(f"Error getting properties for '{blob_name}': {str(e)}")
            return None
            
    def list_models(self, container_name, prefix=None):
        """
        List models in a container
        
        Args:
            container_name: Name of the container (e.g., 'models')
            prefix: Optional prefix to filter blobs by
            
        Returns:
            List of blob names
        """
        try:
            container_client = self._client.get_container_client(container_name)
            return [blob.name for blob in container_client.list_blobs(name_starts_with=prefix)]
        except Exception as e:
            logger.error(f"Error listing models in '{container_name}': {str(e)}")
            return []

# Helper functions
def download_model(container_name, blob_name, local_path=None, check_md5=True):
    """Convenience function to download a model from Azure Blob Storage"""
    return AzureBlobHelper().download_model(container_name, blob_name, local_path, check_md5)

def list_models(container_name, prefix=None):
    """Convenience function to list models in Azure Blob Storage"""
    return AzureBlobHelper().list_models(container_name, prefix) 