# API Integration Tests

This directory contains tests for external API integrations used by the AI Fashion Advisor:

1. **Qdrant** - Vector database for similarity search
2. **Aiven MySQL** - Relational database for structured data
3. **FASHN.AI** - Fashion-specific AI services 
4. **OpenAI** - Large language model and image generation

## Configuration

### Azure Key Vault (Recommended)

These tests are configured to use Azure Key Vault for secrets management. The tests will look for secrets in the following format:

- `QDRANT-URL` - URL for Qdrant database
- `QDRANT-API-KEY` - API key for Qdrant
- `MYSQL-HOST` - MySQL database host
- `MYSQL-PORT` - MySQL database port
- `MYSQL-USER` - MySQL username
- `MYSQL-PASSWORD` - MySQL password
- `MYSQL-DATABASE` - MySQL database name
- `FASHN-AI-API-URL` - FASHN.AI API URL
- `FASHN-AI-API-KEY` - FASHN.AI API key
- `OPENAI-API-KEY` - OpenAI API key

To configure Azure Key Vault access, set the following environment variable:

```bash
# Azure Key Vault URL
export AZURE_KEYVAULT_URL=https://your-key-vault.vault.azure.net/
```

The tests use DefaultAzureCredential for authentication, which supports various authentication methods including managed identity, environment variables, and the Azure CLI.

### Environment Variables (Fallback)

If a secret is not found in Azure Key Vault, the tests will fall back to using environment variables:

```bash
# Qdrant
export QDRANT_URL=https://your-qdrant-instance.com
export QDRANT_API_KEY=your-api-key

# MySQL
export MYSQL_HOST=your-mysql-host.aiven.com
export MYSQL_PORT=12345
export MYSQL_USER=avnadmin
export MYSQL_PASSWORD=your-password
export MYSQL_DATABASE=fashion_advisor

# FASHN.AI
export FASHN_AI_API_URL=https://api.fashn.ai/v1
export FASHN_AI_API_KEY=your-api-key

# OpenAI
export OPENAI_API_KEY=your-api-key
```

## Running the Tests

To run all API tests:

```bash
# From the project root
python tests/run_tests.py --api

# Or directly with pytest
pytest -v tests/api/
```

To run tests for a specific API:

```bash
# Run Qdrant tests only
pytest -v tests/api/test_qdrant.py

# Run MySQL tests only
pytest -v tests/api/test_mysql.py

# Run FASHN.AI tests only
pytest -v tests/api/test_fashn_ai.py

# Run OpenAI tests only
pytest -v tests/api/test_openai.py
```

## Test Markers

These tests use the following pytest markers:

- `api`: All API tests have this marker
- `live`: Tests that require actual services to be running

## Adding New API Tests

When adding tests for a new API:

1. Create a new file with the naming convention `test_[api_name].py`
2. Add appropriate fixtures for authentication and API clients
3. Add tests for basic connectivity and core functionality
4. Make sure to add proper cleanup to avoid leaving test data in production services 