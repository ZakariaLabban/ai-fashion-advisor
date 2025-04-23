import os
import base64
import tempfile
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class AzureKeyVaultHelper:
    """
    Helper class to access secrets from Azure Key Vault.
    This class provides a centralized way to access secrets for all services.
    """
    _instance = None
    _client = None
    _cache = {}
    _temp_files = {}  # Track temp files for cleanup

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AzureKeyVaultHelper, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the Azure Key Vault client"""
        # Get Key Vault URL from environment variable or use a default for local development
        vault_url = os.environ.get("AZURE_KEYVAULT_URL", None)
        
        if not vault_url:
            raise ValueError("AZURE_KEYVAULT_URL environment variable must be set")
            
        # Create a credential using DefaultAzureCredential
        # This will try different authentication methods (managed identity, environment variables, etc.)
        credential = DefaultAzureCredential()
        
        # Create the client
        self._client = SecretClient(vault_url=vault_url, credential=credential)
        
    def get_secret(self, secret_name, default=None):
        """
        Get a secret from Azure Key Vault
        
        Args:
            secret_name: Name of the secret to retrieve
            default: Default value to return if secret is not found or an error occurs
            
        Returns:
            The secret value as a string, or the default value
        """
        # Check if secret is in cache first
        if secret_name in self._cache:
            return self._cache[secret_name]
            
        try:
            # Get the secret from Key Vault
            secret = self._client.get_secret(secret_name)
            
            # Cache the secret
            self._cache[secret_name] = secret.value
            
            return secret.value
        except Exception as e:
            print(f"Error retrieving secret '{secret_name}': {str(e)}")
            return default
            
    def get_multiple_secrets(self, secret_names, defaults=None):
        """
        Get multiple secrets from Azure Key Vault
        
        Args:
            secret_names: List of secret names to retrieve
            defaults: Dictionary of default values keyed by secret name
            
        Returns:
            Dictionary of secret values keyed by secret name
        """
        if defaults is None:
            defaults = {}
            
        result = {}
        for name in secret_names:
            result[name] = self.get_secret(name, defaults.get(name))
            
        return result
    
    def get_file_from_base64_secret(self, secret_name, default_path=None, prefix=None, suffix=None):
        """
        Get a Base64-encoded file from Azure Key Vault and save it to a temporary file
        
        Args:
            secret_name: Name of the secret containing the Base64-encoded file
            default_path: Path to use if the secret is not found
            prefix: Prefix for the temporary file
            suffix: Suffix for the temporary file (e.g., ".json", ".pem")
            
        Returns:
            Path to the temporary file containing the decoded content, or default_path if the secret is not found
        """
        # Check if the file path is already in the cache
        if secret_name in self._temp_files:
            return self._temp_files[secret_name]
            
        # If a default path is provided and exists, use it
        if default_path and os.path.exists(default_path):
            return default_path
            
        # Try to get the Base64-encoded content from Key Vault
        base64_content = self.get_secret(secret_name)
        
        if not base64_content:
            print(f"Base64 secret '{secret_name}' not found, using default path: {default_path}")
            return default_path
            
        try:
            # Decode the Base64 content
            file_content = base64.b64decode(base64_content)
            
            # Create a temporary file
            fd, temp_path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
            
            # Write the decoded content to the temporary file
            with os.fdopen(fd, 'wb') as f:
                f.write(file_content)
                
            # Cache the temporary file path
            self._temp_files[secret_name] = temp_path
            
            print(f"Created temporary file from Base64 secret '{secret_name}': {temp_path}")
            return temp_path
        except Exception as e:
            print(f"Error creating file from Base64 secret '{secret_name}': {str(e)}")
            return default_path
    
    def cleanup_temp_files(self):
        """Clean up temporary files created by get_file_from_base64_secret"""
        for secret_name, temp_path in self._temp_files.items():
            try:
                os.remove(temp_path)
                print(f"Removed temporary file for secret '{secret_name}': {temp_path}")
            except Exception as e:
                print(f"Error removing temporary file for secret '{secret_name}': {str(e)}")
        
        self._temp_files = {}

# Simple usage example:
def get_secret(secret_name, default=None):
    """Convenience function to get a secret from Azure Key Vault"""
    return AzureKeyVaultHelper().get_secret(secret_name, default)

def get_file_from_base64_secret(secret_name, default_path=None, prefix=None, suffix=None):
    """Convenience function to get a file from a Base64-encoded secret"""
    return AzureKeyVaultHelper().get_file_from_base64_secret(secret_name, default_path, prefix, suffix) 