#!/bin/bash
# Script to run integration tests against an existing Immich server

set -e

# Check for required environment variables
if [ -z "$IMMICH_TEST_SERVER_URL" ]; then
  echo "Error: IMMICH_TEST_SERVER_URL environment variable is required"
  echo "Please set it to the URL of your Immich server (e.g., https://immich.example.com)"
  exit 1
fi

if [ -z "$IMMICH_TEST_API_KEY" ]; then
  echo "Error: IMMICH_TEST_API_KEY environment variable is required"
  echo "Please set it to a valid API key for your Immich server"
  exit 1
fi

# Default values
TEST_PATH="tests/integration"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --test-path)
      TEST_PATH="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --test-path PATH    Path to integration tests (default: tests/integration)"
      echo "  --help              Show this help message"
      echo ""
      echo "Required environment variables:"
      echo "  IMMICH_TEST_SERVER_URL     URL of your Immich server (e.g., https://immich.example.com)"
      echo "  IMMICH_TEST_API_KEY      API key for your Immich server"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done


# Create test_files directory if it doesn't exist
mkdir -p tests/integration/test_files

# Create a sample test image if PIL is available
if ! poetry run python -c "import PIL" &>/dev/null; then
  echo "PIL not available, attempting to install..."
  pip install pillow
fi

if [ ! -f "tests/integration/test_files/test_image.jpg" ] && poetry run python -c "import PIL" &>/dev/null; then
  echo "Creating sample test image..."
  poetry run python -c "from PIL import Image; img = Image.new('RGB', (100, 100), color='red'); img.save('tests/integration/test_files/test_image.jpg')"
fi

# Check if the server is reachable
echo "Checking connection to Immich server at $IMMICH_TEST_SERVER_URL..."
if ! poetry run python -c "
import httpx
try:
    response = httpx.get('$IMMICH_TEST_SERVER_URL/api/server/ping', timeout=5)
    if response.status_code == 200 and response.json().get('res') == 'pong':
        exit(0)
except httpx.RequestError:
    pass
exit(1)
" &>/dev/null; then
  echo "Error: Could not connect to Immich server at $IMMICH_TEST_SERVER_URL"
  echo "Please check that the server is running and the URL is correct"
  exit 1
fi
echo "Successfully connected to Immich server!"

# Run the tests
echo "Running integration tests..."
poetry run python -m pytest "$TEST_PATH" -v

echo "Done!"
