# Migrating from .env Files to GitHub Secrets

This guide explains how to migrate your environment variables from a local `.env` file to GitHub Secrets for more secure deployment and CI/CD workflows.

## Step 1: Identify Environment Variables

Your application uses the following environment variables that need to be migrated to GitHub Secrets:

- **API Keys and Endpoints:**
  - `FASHN_AI_API_KEY`
  - `FASHN_AI_BASE_URL`
  - `OPENAI_API_KEY`
  - `QDRANT_URL`
  - `QDRANT_API_KEY`
  - `COLLECTION_NAME`

- **Google-related Configuration:**
  - `GOOGLE_SERVICE_ACCOUNT_FILE`
  - `GOOGLE_FOLDER_ID`
  - `SEGMENTED_FOLDER_ID`
  - `FULL_FOLDER_ID`
  - `SERVICE_ACCOUNT_FILE`

- **Database Configuration:**
  - `MYSQL_HOST`
  - `MYSQL_PORT`
  - `MYSQL_USER`
  - `MYSQL_PASSWORD`
  - `MYSQL_DATABASE`
  - `MYSQL_SSL_CA`

## Step 2: Create GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. For each environment variable listed above:
   - **Name**: Use the same name as in your `.env` file (e.g., `OPENAI_API_KEY`)
   - **Value**: Copy the value from your `.env` file
5. Click **Add secret**

## Step 3: Update GitHub Workflows

Your GitHub Actions workflow file (`.github/workflows/main.yml`) has been updated to reference these secrets:

```yaml
steps:
  - name: Set up environment
    run: |
      # Create .env file from GitHub Secrets
      echo "# Environment file generated from GitHub Secrets" > .env
      echo "FASHN_AI_API_KEY=${{ secrets.FASHN_AI_API_KEY }}" >> .env
      echo "FASHN_AI_BASE_URL=${{ secrets.FASHN_AI_BASE_URL }}" >> .env
      echo "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" >> .env
      echo "QDRANT_URL=${{ secrets.QDRANT_URL }}" >> .env
      echo "QDRANT_API_KEY=${{ secrets.QDRANT_API_KEY }}" >> .env
      echo "COLLECTION_NAME=${{ secrets.COLLECTION_NAME }}" >> .env
      echo "GOOGLE_SERVICE_ACCOUNT_FILE=${{ secrets.GOOGLE_SERVICE_ACCOUNT_FILE }}" >> .env
      echo "GOOGLE_FOLDER_ID=${{ secrets.GOOGLE_FOLDER_ID }}" >> .env
      echo "MYSQL_HOST=${{ secrets.MYSQL_HOST }}" >> .env
      echo "MYSQL_PORT=${{ secrets.MYSQL_PORT }}" >> .env
      echo "MYSQL_USER=${{ secrets.MYSQL_USER }}" >> .env
      echo "MYSQL_PASSWORD=${{ secrets.MYSQL_PASSWORD }}" >> .env
      echo "MYSQL_DATABASE=${{ secrets.MYSQL_DATABASE }}" >> .env
      echo "MYSQL_SSL_CA=${{ secrets.MYSQL_SSL_CA }}" >> .env
      echo "SEGMENTED_FOLDER_ID=${{ secrets.SEGMENTED_FOLDER_ID }}" >> .env
      echo "FULL_FOLDER_ID=${{ secrets.FULL_FOLDER_ID }}" >> .env
      echo "SERVICE_ACCOUNT_FILE=${{ secrets.SERVICE_ACCOUNT_FILE }}" >> .env
```

## Step 4: Update Docker Compose Configuration

For local development, continue using your `.env` file.

For production deployment, your `docker-compose.yml` already uses environment variables from the `.env` file for these services:
- virtual-tryon-iep
- elegance-iep
- reco-data-iep
- text2image-iep

## Step 5: Test Your Configuration

1. Push your changes to GitHub
2. Check that your GitHub Actions workflow is correctly setting up the environment variables
3. Verify that your application can successfully access the secrets

## Special Notes for File-Based Secrets

The following variables refer to files and need special handling:
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `SERVICE_ACCOUNT_FILE` 
- `MYSQL_SSL_CA`

For these files, you need to encode the file content as a base64 string:

### For Linux/Mac:
```bash
# For the service account file
base64 -w 0 auradataset-a28919b443a7.json > service_account_base64.txt

# For the MySQL SSL CA certificate
base64 -w 0 ca.pem > mysql_ca_base64.txt
```

### For Windows:
```powershell
# For the service account file
[Convert]::ToBase64String([IO.File]::ReadAllBytes("auradataset-a28919b443a7.json")) | Out-File -NoNewline service_account_base64.txt

# For the MySQL SSL CA certificate
[Convert]::ToBase64String([IO.File]::ReadAllBytes("ca.pem")) | Out-File -NoNewline mysql_ca_base64.txt
```

Then add these as GitHub Secrets:
- `SERVICE_ACCOUNT_FILE_CONTENT`: The content of service_account_base64.txt
- `MYSQL_SSL_CA_CONTENT`: The content of mysql_ca_base64.txt

In the workflow, we set the environment variables to point to the file paths:
```yaml
echo "GOOGLE_SERVICE_ACCOUNT_FILE=./auradataset-a28919b443a7.json" >> .env
echo "SERVICE_ACCOUNT_FILE=./auradataset-a28919b443a7.json" >> .env
echo "MYSQL_SSL_CA=./ca.pem" >> .env
```

And then we create these files from the base64-encoded secrets:
```yaml
# Decode the base64-encoded service account file
echo "${{ secrets.SERVICE_ACCOUNT_FILE_CONTENT }}" | base64 -d > auradataset-a28919b443a7.json

# Create the MySQL SSL CA file
echo "${{ secrets.MYSQL_SSL_CA_CONTENT }}" | base64 -d > ca.pem
```

The workflow will automatically decode these secrets and create the necessary files during deployment.

## Security Best Practices

- Never commit `.env` files to your repository
- Regularly rotate your secrets
- Use GitHub's secret scanning to detect any accidentally committed secrets
- Limit access to repository secrets to only those who need it