# Immich Python Client

A Python client library and CLI for interacting with the [Immich](https://immich.app/) API.

## 🚀 TLDR

```bash
immich-py -e 'https://pics.my.server.com' -k 'abc123' asset upload <directory-or-archive-path> --recursive
```

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
immich-py --endpoint "https://your-immich-server.com" --api-key "your-api-key" <command>
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
immich-py --help
immich-py server --help
immich-py asset --help
immich-py album --help
immich-py tag --help
immich-py job --help
```

### Examples

#### Server Commands

```bash
# Ping the server
immich-py server ping

# Get server statistics
immich-py server stats

# Get asset statistics
immich-py server asset-stats

# Get supported media types
immich-py server media-types

# Get server information
immich-py server about

# Check if a file extension is supported
immich-py server check-extension .jpg
```

#### Asset Commands

```bash
# List assets
immich-py asset list

# Get information about an asset
immich-py asset info <asset-id>

# Download an asset
immich-py asset download <asset-id> --output <output-path>

# Upload an asset
immich-py asset upload <file-path>

# Upload a directory or archive of assets recursively
immich-py asset upload <directory-or-archive-path> --recursive

# Upload with a sidecar file (for single file uploads)
immich-py asset upload <file-path> --sidecar-path <sidecar-path>

# Upload and add to albums (creates albums if they don't exist)
immich-py asset upload <file-path> --album "Vacation" --album "Family"

# Upload recursively and add all assets to albums
immich-py asset upload <directory-or-archive-path> --recursive --album "Summer 2024"

# Delete assets
immich-py asset delete <asset-id-1> <asset-id-2> ...

# Update an asset
immich-py asset update <asset-id> --favorite --description "New description"

# Update multiple assets
immich-py asset batch-update <asset-id-1> <asset-id-2> ... --favorite
```

#### Album Commands

```bash
# List albums
immich-py album list

# Get information about an album
immich-py album info <album-id>

# Create an album
immich-py album create "My Album" --description "My album description" --asset-id <asset-id-1> --asset-id <asset-id-2>

# Add assets to an album
immich-py album add-assets <album-id> <asset-id-1> <asset-id-2> ...

# Delete an album
immich-py album delete <album-id>

# Get albums that an asset belongs to
immich-py album asset-albums <asset-id>
```

#### Tag Commands

```bash
# List tags
immich-py tag list

# Create or update tags
immich-py tag create "tag1" "tag2" "tag3"

# Tag assets
immich-py tag tag-assets <tag-id> <asset-id-1> <asset-id-2> ...

# Tag multiple assets with multiple tags
immich-py tag bulk-tag-assets --tag-id <tag-id-1> --tag-id <tag-id-2> <asset-id-1> <asset-id-2> ...
```

#### Job Commands

```bash
# List jobs
immich-py job list

# Send a command to a job
immich-py job command <job-id> <command> --force

# Create a job
immich-py job create <job-name>
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

# Create an album and add assets to it
album = album_api.create_album("Vacation Photos")
album_api.add_assets_to_album(album.id, ["asset-id-1", "asset-id-2"])
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

### Building the Executable

The project includes support for building a standalone executable using PyInstaller. This is useful for distributing the CLI without requiring users to install Python or any dependencies.

```bash
# Build the executable
poetry run build-executable
```

This will create an executable in the `build/executable` directory.

#### GitHub Release Integration

The project includes a GitHub workflow that automatically builds executables for Windows, macOS, and Linux when a new release is created on GitHub. The executables are attached to the release as assets.

To create a new release:

1. Create a new tag and push it to GitHub
2. Create a new release on GitHub using the tag
3. The workflow will automatically build and attach the executables to the release

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
