# Azure Key Vault Migration Guide

This guide provides instructions for migrating from using `.env` files to Azure Key Vault for securely storing and accessing secrets in the AI Fashion Advisor application.

## Migration Overview

1. Create an Azure Key Vault
2. Store your secrets in Azure Key Vault
3. Configure Azure authentication
4. Update your local environment with Azure Key Vault URL
5. Deploy the updated application

## 1. Create an Azure Key Vault

1. Sign in to the [Azure Portal](https://portal.azure.com)
2. Search for "Key vaults" and click on "Create key vault"
3. Fill in the required details:
   - Resource group: Create a new one or use an existing one
   - Key vault name: Choose a globally unique name
   - Region: Select a region close to your deployment
   - Pricing tier: Standard
4. Review and create the Key Vault

## 2. Store Your Secrets in Azure Key Vault

For each environment variable in your `.env` file, create a corresponding secret in Azure Key Vault:

1. Navigate to your Key Vault in the Azure Portal
2. Select "Secrets" from the left menu
3. Click "+ Generate/Import"
4. Create each secret with the following naming convention:
   - Replace underscores (`_`) with hyphens (`-`)
   - Use all uppercase for consistency

For example:
- `FASHN_AI_API_KEY` becomes `FASHN-AI-API-KEY`
- `MYSQL_PASSWORD` becomes `MYSQL-PASSWORD`

### Handling Binary Files (SSL Certificates and Service Account JSON)

For binary files like the MySQL SSL certificate and Google service account JSON, you need to convert them to Base64 strings:

1. **Convert the files to Base64 strings**:
   ```bash
   # For service account JSON (run this in the directory where the JSON file is located)
   cat auradataset-a28919b443a7.json | base64 -w 0 > service-account-base64.txt

   # For SSL certificate
   cat ca.pem | base64 -w 0 > ca-pem-base64.txt
   ```

2. **Copy the Base64 string from the text file**:
   ```bash
   # Open and copy the content 
   cat service-account-base64.txt
   cat ca-pem-base64.txt
   ```

3. **Store these Base64 strings in Azure Key Vault** with special suffix:
   - Key: `SERVICE-ACCOUNT-FILE-BASE64` (content: the Base64 string from service-account-base64.txt)
   - Key: `MYSQL-SSL-CA-BASE64` (content: the Base64 string from ca-pem-base64.txt)

The updated `azure_keyvault_helper.py` includes a method called `get_file_from_base64_secret` that will:
- Get the Base64-encoded string from Key Vault
- Decode it
- Write it to a temporary file
- Return the path to this file for use in your application

#### Alternative for SSL Certificates: Using Azure Key Vault Certificates

For SSL certificates specifically, Azure Key Vault offers built-in certificate management:

1. **Import the certificate to Azure Key Vault**:
   - In Azure Portal, go to your Key Vault
   - Select "Certificates" from the left menu
   - Click "+ Generate/Import" 
   - Choose "Import" method
   - Upload your ca.pem file
   - Name it `MYSQL-SSL-CA`

2. **To access the certificate programmatically**:
   ```python
   from azure.keyvault.certificates import CertificateClient
   
   # Create a certificate client
   certificate_client = CertificateClient(vault_url=vault_url, credential=credential)
   
   # Get the certificate
   certificate = certificate_client.get_certificate("MYSQL-SSL-CA")
   
   # Access certificate properties
   cert_version = certificate.properties.version
   
   # Download the certificate
   downloaded_certificate = certificate_client.download_certificate(name="MYSQL-SSL-CA")
   
   # Write to a temporary file
   with open("temp_ca.pem", "wb") as f:
       f.write(downloaded_certificate.cer)
   ```

This approach provides better certificate lifecycle management, automatic renewal, and versioning capabilities.

Here's a list of all secrets you should migrate:

```
FASHN-AI-API-KEY
FASHN-AI-BASE-URL
OPENAI-API-KEY
MYSQL-HOST
MYSQL-PORT
MYSQL-USER
MYSQL-PASSWORD
MYSQL-DATABASE
QDRANT-URL
QDRANT-API-KEY
COLLECTION-NAME
SEGMENTED-FOLDER-ID
FULL-FOLDER-ID
CONVERSATIONS-FOLDER
SERVICE-ACCOUNT-FILE-BASE64  # Base64-encoded JSON file
MYSQL-SSL-CA-BASE64          # Base64-encoded ca.pem file
```

## 3. Configure Azure Authentication

You have several options for authentication:

### Option A: Managed Identity (Recommended for Production)

If deploying to Azure services like App Service or AKS:

1. Enable managed identity for your service
2. Grant the managed identity access to your Key Vault:
   - Go to your Key Vault → Access policies
   - Add Access Policy
   - Select "Get" and "List" permissions for Secrets
   - Select the managed identity of your service

### Option B: Service Principal (For non-Azure deployments)

1. Create a service principal:
   ```bash
   az ad sp create-for-rbac --name "fashion-advisor-kv-access" --skip-assignment
   ```
2. Note the appId, password, and tenant values
3. Grant the service principal access to your Key Vault:
   - Go to your Key Vault → Access policies
   - Add Access Policy
   - Select "Get" and "List" permissions for Secrets
   - Select the service principal you created
4. Add these values to your environment variables:
   ```
   AZURE_TENANT_ID=<tenant-id>
   AZURE_CLIENT_ID=<app-id>
   AZURE_CLIENT_SECRET=<password>
   ```

## 4. Update Your Local Environment

Create a new `.env` file with just the Azure Key Vault URL and authentication info (if using service principal):

```
AZURE_KEYVAULT_URL=https://<your-key-vault-name>.vault.azure.net/
# Only needed for service principal authentication
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<app-id>
AZURE_CLIENT_SECRET=<password>
```

A sample file is provided as `azure.env.example` which you can copy and modify.

## 5. Deploy the Updated Application

1. Ensure the `azure_keyvault_helper.py` file is in your project root
2. Update all services' requirements.txt files with Azure SDK dependencies:
   ```
   azure-identity==1.14.0
   azure-keyvault-secrets==4.7.0
   ```
3. Start the application using docker-compose:
   ```bash
   docker-compose up -d
   ```

## Verification

To verify the migration was successful:

1. Check the logs for each service to ensure they are connecting to Azure Key Vault
2. Verify the health endpoints are returning successful responses
3. Test the application functionality to ensure it works as expected

## Rollback Plan

If you encounter issues with the Azure Key Vault integration:

1. Revert to using the `.env` file by removing the Azure SDK imports
2. Restore the original environment variable loading code
3. Update the docker-compose.yml file to use the `.env` file again

## Additional Resources

- [Azure Key Vault Documentation](https://docs.microsoft.com/en-us/azure/key-vault/)
- [DefaultAzureCredential Documentation](https://docs.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential) 