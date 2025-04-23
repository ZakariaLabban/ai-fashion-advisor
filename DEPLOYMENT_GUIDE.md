# Deployment Guide for AI Fashion Advisor

This guide explains how to deploy the AI Fashion Advisor application using GitHub Secrets for secure environment variable management.

## Local Development

For local development, you will continue using a `.env` file in the root directory:

1. Create a `.env` file in the project root with all required environment variables:
   ```
   FASHN_AI_API_KEY=your_key_here
   FASHN_AI_BASE_URL=your_url_here
   OPENAI_API_KEY=your_key_here
   QDRANT_URL=your_qdrant_url
   QDRANT_API_KEY=your_qdrant_key
   COLLECTION_NAME=your_collection
   GOOGLE_FOLDER_ID=your_folder_id
   MYSQL_HOST=your_mysql_host
   MYSQL_PORT=your_mysql_port
   MYSQL_USER=your_mysql_user
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DATABASE=your_mysql_database
   SEGMENTED_FOLDER_ID=your_segmented_folder_id
   FULL_FOLDER_ID=your_full_folder_id
   
   # These paths must match the Docker volume mounts
   MYSQL_SSL_CA=/app/ca.pem
   SERVICE_ACCOUNT_FILE=/app/auradataset-a28919b443a7.json
   ```

2. Place the required service account files in their respective locations:
   - Service account JSON file: 
     - `reco_data_iep/auradataset-a28919b443a7.json`
     - `text2image_iep/auradataset-a28919b443a7.json`
   - MySQL SSL CA certificate: 
     - `reco_data_iep/ca.pem`

3. Run the application locally using Docker Compose:
   ```
   docker-compose up -d
   ```

## Production Deployment

For production deployment, we use GitHub Secrets to securely manage environment variables:

1. **Set up GitHub Secrets**:
   - Follow the instructions in `GITHUB_SECRETS_MIGRATION.md` to create all required secrets
   - Make sure to encode file contents (service account, CA cert) as base64 and add them as:
     - `SERVICE_ACCOUNT_FILE_CONTENT`
     - `MYSQL_SSL_CA_CONTENT`

2. **Use GitHub Actions for Deployment**:
   - The workflow in `.github/workflows/main.yml` will:
     - Create a `.env` file with values from GitHub Secrets
     - Decode and create necessary files in the correct locations:
       - `reco_data_iep/auradataset-a28919b443a7.json`
       - `text2image_iep/auradataset-a28919b443a7.json`
       - `reco_data_iep/ca.pem`
     - Build and deploy the application

3. **Test Your Configuration**:
   - Run the test workflow (`.github/workflows/test-secrets.yml`) to verify all secrets are set correctly
   - This can be triggered manually from the GitHub Actions tab

## File Structure for Environment Variables

```
ai-fashion-advisor/
├── .env                      # Created by GitHub Actions or manually for local dev
├── .github/
│   └── workflows/
│       ├── main.yml         # Main deployment workflow
│       └── test-secrets.yml # Test workflow
├── reco_data_iep/
│   ├── ca.pem               # MySQL SSL CA certificate
│   └── auradataset-a28919b443a7.json  # Google service account file
├── text2image_iep/
│   └── auradataset-a28919b443a7.json  # Google service account file (copy)
└── docker-compose.yml       # Docker configuration
```

## Maintaining Different Environments

For managing multiple environments (e.g., staging, production):

### Option 1: Environment Variables in GitHub Actions

Use GitHub Environments to manage different sets of secrets:

1. Create environments in your GitHub repository (e.g., staging, production)
2. Add appropriate secrets to each environment
3. Update your workflow to use the appropriate environment:
   ```yaml
   jobs:
     deploy:
       environment: production # or staging
       runs-on: ubuntu-latest
       steps:
         # ... deployment steps
   ```

### Option 2: Branch-Based Deployments

Deploy to different environments based on branches:

```yaml
on:
  push:
    branches:
      - main        # Production
      - staging     # Staging environment
```

## Troubleshooting

If you encounter issues with secrets not being available or files not being created:

1. Check GitHub Actions logs to see which secrets are missing
2. Verify that file content is properly base64-encoded
3. Ensure service account files and CA certificates are valid
4. Verify that volume mounts in docker-compose.yml point to the correct locations

## Security Notes

- Never commit `.env` files to your repository
- Regularly rotate your secrets and API keys
- Use GitHub's secret scanning to detect any accidentally committed secrets
- Limit access to repository secrets to only those who need it 