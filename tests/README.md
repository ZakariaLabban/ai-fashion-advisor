# AI Fashion Advisor Tests

This directory contains tests for the AI Fashion Advisor project.

## Test Structure

The tests are organized into three categories:

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test the interaction between multiple components
3. **End-to-End Tests** - Test the entire system from user input to output

## Running Tests

To run the tests, use the `run_tests.py` script:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --unit

# Run only integration tests
python run_tests.py --integration

# Run only end-to-end tests
python run_tests.py --e2e

# Run tests for a specific service
python run_tests.py --service=detection
python run_tests.py --service=style
python run_tests.py --service=feature
python run_tests.py --service=match
python run_tests.py --service=tryon
python run_tests.py --service=elegance
python run_tests.py --service=reco

# Run specific test file
pytest -v unit/test_detection_iep.py

# Run with coverage report
pytest --cov=../eep --cov=../detection_iep --cov-report=term-missing
```

## Fixtures

The `conftest.py` file contains common fixtures used across tests:

- **Test Images**: Mock images for testing (automatically generated if needed)
- **HTTP Clients**: Both sync and async clients for making HTTP requests
- **Response Mocks**: Sample valid responses for testing

## Mocking Strategy

The tests use mocking to avoid dependencies on external services:

1. **Unit Tests**: Mock the HTTPX client to simulate responses from the services it directly depends on.
2. **Integration Tests**: Mock the EEP service, as it would call multiple IEPs in sequence.
3. **End-to-End Tests**: These would typically run against a deployed system, but for convenience, they are also mocked in this test suite.

## Adding Tests

When adding new tests:

1. Add unit tests for new components in the appropriate directory
2. Update integration tests to cover interaction with the new components
3. Make sure all tests use the correct markers for categorization
4. Update any fixtures in `conftest.py` as needed

## Test Data

Test images are generated programmatically to avoid committing binary files to the repository. If you need to add specific test cases, consider adding them to the `conftest.py` file as fixtures.

## Continuous Integration

Tests are automatically run on GitHub Actions for each pull request.

For questions about the test suite, contact the project maintainers. 