"""
Helper module to read environment variables from docker-compose.yml.
This is used by the API tests to read AZURE_KEYVAULT_URL and other variables.
"""

import os
import yaml
from pathlib import Path

def read_env_from_docker_compose(var_name, default=None):
    """
    Read an environment variable from docker-compose.yml if it's not in the environment.
    
    Args:
        var_name: The name of the environment variable to read
        default: The default value to return if the variable is not found
    
    Returns:
        The value of the environment variable, or the default value
    """
    # First check environment
    value = os.getenv(var_name)
    if value:
        return value
        
    # Try to read from docker-compose.yml
    try:
        docker_compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
        if docker_compose_path.exists():
            with open(docker_compose_path, 'r') as f:
                docker_compose = yaml.safe_load(f)
                
            # Search for the variable in all services
            for service_name, service_data in docker_compose.get('services', {}).items():
                env_vars = service_data.get('environment', [])
                if isinstance(env_vars, list):
                    # List format: ["VAR=value", ...]
                    for env_var in env_vars:
                        if isinstance(env_var, str) and env_var.startswith(f"{var_name}="):
                            value = env_var.split('=', 1)[1]
                            print(f"Found {var_name} in docker-compose.yml: {value}")
                            return value
                elif isinstance(env_vars, dict):
                    # Dict format: {VAR: value, ...}
                    if var_name in env_vars:
                        value = env_vars[var_name]
                        print(f"Found {var_name} in docker-compose.yml: {value}")
                        return value
                
                # Check if it's in env_file
                env_file = service_data.get('env_file')
                if env_file:
                    if isinstance(env_file, list):
                        env_files = env_file
                    else:
                        env_files = [env_file]
                    
                    for ef in env_files:
                        ef_path = Path(__file__).parent.parent.parent / ef
                        if ef_path.exists():
                            with open(ef_path, 'r') as env_f:
                                for line in env_f:
                                    if line.strip().startswith(f"{var_name}="):
                                        value = line.strip().split('=', 1)[1]
                                        print(f"Found {var_name} in {ef}: {value}")
                                        return value
    except Exception as e:
        print(f"Error reading docker-compose.yml: {e}")
    
    return default


def setup_azure_keyvault():
    """
    Setup Azure Key Vault environment variable.
    This sets AZURE_KEYVAULT_URL from docker-compose.yml if it's not in the environment.
    
    Returns:
        The AZURE_KEYVAULT_URL, or None if not found
    """
    AZURE_KEYVAULT_URL = read_env_from_docker_compose("AZURE_KEYVAULT_URL")
    
    if not AZURE_KEYVAULT_URL:
        print("WARNING: AZURE_KEYVAULT_URL is not set. Tests requiring Azure Key Vault will be skipped.")
        return None
    
    # Set the environment variable for the Azure SDK
    os.environ["AZURE_KEYVAULT_URL"] = AZURE_KEYVAULT_URL
    return AZURE_KEYVAULT_URL 