# Integration Tests for immich-py

This directory contains integration tests for the immich-py library. These tests interact with a real Immich server.

## Prerequisites

- Access to an Immich server
- API key for the Immich server
- Python 3.12+
- Poetry (for dependency management)
- PIL/Pillow (optional, for creating test images)

## Setup

The integration tests require access to a running Immich server and a valid API key.

```bash
# Install dependencies
poetry install

# Create test files directory
mkdir -p tests/integration/test_files

# Create a test image (if you have PIL installed)
poetry run python -c "from PIL import Image; img = Image.new('RGB', (100, 100), color='red'); img.save('tests/integration/test_files/test_image.jpg')"
```

## Running Tests

You can run the integration tests using the provided script:

```bash
# Set environment variables for your Immich server
export IMMICH_TEST_SERVER_URL="https://your-immich-server.com"
export IMMICH_TEST_API_KEY="your-api-key"

# Run the tests
./scripts/run_integration_tests.sh
```

This script will:
1. Check that the required environment variables are set
2. Verify that the Immich server is reachable
3. Run the integration tests

### Script Options

```
Usage: ./scripts/run_integration_tests.sh [options]
Options:
  --test-path PATH    Path to integration tests (default: tests/integration)
  --help              Show this help message

Required environment variables:
  IMMICH_TEST_SERVER_URL     URL of your Immich server (e.g., https://immich.example.com)
  IMMICH_TEST_API_KEY      API key for your Immich server
```

### Running Tests Manually

If you prefer to run the tests directly with pytest:

```bash
# Set environment variables
export IMMICH_TEST_SERVER_URL="https://your-immich-server.com"
export IMMICH_TEST_API_KEY="your-api-key"

# Run the tests
python -m pytest tests/integration -v
```

## API Key

The integration tests require an API key to authenticate with the Immich server. You need to:

1. Log in to your Immich server
2. Go to Settings > API Keys
3. Create a new API key
4. Use this key in the `IMMICH_TEST_API_KEY` environment variable

## Test Files

The integration tests use test files (images, videos) for testing asset-related functionality. These files should be placed in the `tests/integration/test_files` directory.

- `test_image.jpg`: A test image (can be created using PIL)
- `test_video.mp4`: A test video (optional)

## Writing Integration Tests

When writing integration tests:

1. Use the `integration_client` fixture to get an authenticated client
2. Use the `test_image_path` and `test_video_path` fixtures to get paths to test files
3. Clean up any resources created during tests

Example:

```python
def test_something(integration_client, test_image_path):
    # Use the client to interact with the server
    result = integration_client.some_method()

    # Assert something about the result
    assert result is not None
