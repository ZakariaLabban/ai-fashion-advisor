# API Integration Tests

This directory contains tests for external API integrations used by the AI Fashion Advisor:

1. **Qdrant** - Vector database for similarity search
2. **MySQL** - Relational database for structured data
3. **FASHN.AI** - Fashion-specific AI services for virtual try-on
4. **OpenAI** - Large language model for text generation

## Configuration

### Credential Priority

The tests follow this order of priority for credentials:

1. **Azure Key Vault** (PRIMARY) - Tests will first attempt to retrieve secrets from Azure Key Vault
2. **Environment Variables** (FALLBACK) - If a secret is not found in Azure Key Vault, tests will check environment variables
3. **Docker Compose** (ADDITIONAL) - For Azure Key Vault URL, tests will also check the `docker-compose.yml` file

This ensures that secret management is secure and centralized, while still allowing for local testing with environment variables when needed.

### Azure Key Vault (Primary)

These tests are configured to use Azure Key Vault for secrets management. The tests will look for secrets in the following format:

- `QDRANT-URL` - URL for Qdrant database
- `QDRANT-API-KEY` - API key for Qdrant
- `MYSQL-HOST` - MySQL database host
- `MYSQL-PORT` - MySQL database port
- `MYSQL-USER` - MySQL username
- `MYSQL-PASSWORD` - MySQL password
- `MYSQL-DATABASE` - MySQL database name
- `FASHN-AI-BASE-URL` or `FASHN-AI-API-URL` - FASHN.AI API URL
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
# Qdrant Cloud
export QDRANT_URL=https://<cluster-id>.<region>.aws.cloud.qdrant.io:6333
export QDRANT_API_KEY=your-qdrant-cloud-api-key

# MySQL
export MYSQL_HOST=your-mysql-host.aiven.com
export MYSQL_PORT=12345
export MYSQL_USER=avnadmin
export MYSQL_PASSWORD=your-password
export MYSQL_DATABASE=fashion_advisor

# FASHN.AI
export FASHN_AI_BASE_URL=https://api.fashn.ai/v1
export FASHN_AI_API_KEY=your-api-key

# OpenAI
export OPENAI_API_KEY=your-api-key
```

### Docker Compose Integration

For the Azure Key Vault URL, tests can now read from the `docker-compose.yml` file in the project root. This allows for a more seamless testing experience when working with dockerized services.

## Dependencies

The dependencies for these tests are included in the main `tests/requirements.txt` file. Install them using:

```bash
# From the tests directory
pip install -r requirements.txt
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

## Test Behavior

These tests are designed to gracefully handle missing connections or credentials:

1. **Missing Credentials**: Tests will be skipped if the necessary API keys or connection parameters are not found in Azure Key Vault or environment variables.

2. **Missing Services**: Tests will be skipped if the services themselves are not available (e.g., if Qdrant is not running on the specified URL).

3. **Missing Image Files**: For tests requiring images (like FASHN.AI), the tests will use default high-quality images from Unsplash rather than relying on local files.

This ensures that the test suite remains functional even when testing in environments where not all services are available.

## Test Markers

These tests use the following pytest markers:

- `api`: All API tests have this marker
- `live`: Tests that require actual services to be running

## API Test Details

### FASHN.AI Tests

The FASHN.AI tests focus on virtual try-on functionality, which is the primary capability we're using from this service. The tests use a polling approach to handle the asynchronous nature of the processing.

Key features of the FASHN.AI tests:
- Tests basic API accessibility without relying on specific endpoints that might change
- Uses high-quality Unsplash images for more reliable pose detection
- Handles common PoseError issues gracefully by skipping tests instead of failing
- Implements robust polling with appropriate timeouts and diagnostics

### OpenAI Tests

The OpenAI tests focus specifically on text-based chat completion functionality used by our fashion advisor system. We test basic connectivity and the ability to generate text responses to fashion-related prompts.

## Adding New API Tests

When adding tests for a new API:

1. Create a new file with the naming convention `test_[api_name].py`
2. Add appropriate fixtures for authentication and API clients
3. Add tests for basic connectivity and core functionality
4. Make sure to add proper cleanup to avoid leaving test data in production services
5. Use `pytest.skip()` for handling missing credentials or services 
6. Import the `docker_env_reader` module to utilize Azure Key Vault URL from docker-compose.yml 