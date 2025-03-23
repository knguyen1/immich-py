# Immich Python Client

A Python client library and CLI for interacting with the [Immich](https://immich.app/) API.

## Installation

```bash
pip install immich-py
```

Or with Poetry:

```bash
poetry add immich-py
```

## CLI Usage

The `immich-py` package provides a command-line interface for interacting with the Immich API.

### Configuration

The CLI requires an API endpoint and an API key. These can be provided as command-line options or as environment variables.

```bash
# Set environment variables
export IMMICH_ENDPOINT="https://your-immich-server.com"
export IMMICH_API_KEY="your-api-key"

# Or provide them as command-line options
immich --endpoint "https://your-immich-server.com" --api-key "your-api-key" <command>
```

### Commands

The CLI provides commands for interacting with various aspects of the Immich API:

- `server`: Commands for interacting with the Immich server
- `asset`: Commands for interacting with assets
- `album`: Commands for interacting with albums
- `tag`: Commands for interacting with tags
- `job`: Commands for interacting with jobs

For more information on a specific command, use the `--help` option:

```bash
immich --help
immich server --help
immich asset --help
immich album --help
immich tag --help
immich job --help
```

### Examples

#### Server Commands

```bash
# Ping the server
immich server ping

# Get server statistics
immich server stats

# Get asset statistics
immich server asset-stats

# Get supported media types
immich server media-types

# Get server information
immich server about

# Check if a file extension is supported
immich server check-extension .jpg
```

#### Asset Commands

```bash
# List assets
immich asset list

# Get information about an asset
immich asset info <asset-id>

# Download an asset
immich asset download <asset-id> --output <output-path>

# Upload an asset
immich asset upload <file-path>

# Upload a directory or archive of assets recursively
immich asset upload <directory-or-archive-path> --recursive

# Upload with a sidecar file (for single file uploads)
immich asset upload <file-path> --sidecar-path <sidecar-path>

# Delete assets
immich asset delete <asset-id-1> <asset-id-2> ...

# Update an asset
immich asset update <asset-id> --favorite --description "New description"

# Update multiple assets
immich asset batch-update <asset-id-1> <asset-id-2> ... --favorite
```

#### Album Commands

```bash
# List albums
immich album list

# Get information about an album
immich album info <album-id>

# Create an album
immich album create "My Album" --description "My album description" --asset-id <asset-id-1> --asset-id <asset-id-2>

# Add assets to an album
immich album add-assets <album-id> <asset-id-1> <asset-id-2> ...

# Delete an album
immich album delete <album-id>

# Get albums that an asset belongs to
immich album asset-albums <asset-id>
```

#### Tag Commands

```bash
# List tags
immich tag list

# Create or update tags
immich tag create "tag1" "tag2" "tag3"

# Tag assets
immich tag tag-assets <tag-id> <asset-id-1> <asset-id-2> ...

# Tag multiple assets with multiple tags
immich tag bulk-tag-assets --tag-id <tag-id-1> --tag-id <tag-id-2> <asset-id-1> <asset-id-2> ...
```

#### Job Commands

```bash
# List jobs
immich job list

# Send a command to a job
immich job command <job-id> <command> --force

# Create a job
immich job create <job-name>
```

## Library Usage

The `immich-py` package can also be used as a library in your Python code.

```python
from immich_py import ImmichClient, AssetAPI, AlbumAPI

# Create a client
client = ImmichClient(
    endpoint="https://your-immich-server.com",
    api_key="your-api-key",
)

# Use the client directly
client.ping_server()

# Or use the API classes
asset_api = AssetAPI(client)
assets = asset_api.get_all_assets()

# Upload a single asset
result = asset_api.upload_asset("path/to/image.jpg")

# Upload multiple assets from a directory or archive
# This can handle directories, zip/tar archives, and individual files
results = asset_api.upload_assets("path/to/directory")
results = asset_api.upload_assets("path/to/archive.zip")
result = asset_api.upload_assets("path/to/image.jpg", sidecar_path="path/to/metadata.json")

album_api = AlbumAPI(client)
albums = album_api.get_all_albums()
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/immich-py.git
cd immich-py

# Install dependencies
poetry install

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
# Run unit tests
poetry run pytest tests/unit

# Run integration tests (requires access to an Immich server)
export IMMICH_TEST_SERVER_URL="https://your-immich-server.com"
export IMMICH_TEST_API_KEY="your-api-key"
./scripts/run_integration_tests.sh
```

#### Integration Tests

The project includes integration tests that run against a real Immich server instance. These tests verify that the client works correctly with an actual Immich server.

To run the integration tests:

1. Make sure you have access to an Immich server and an API key
2. Set the required environment variables:
   ```bash
   export IMMICH_TEST_SERVER_URL="https://your-immich-server.com"
   export IMMICH_TEST_API_KEY="your-api-key"
   ```
3. Run the integration test script:
   ```bash
   ./scripts/run_integration_tests.sh
   ```

For more details on the integration tests, see [tests/integration/README.md](tests/integration/README.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
