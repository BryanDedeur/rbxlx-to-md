# rbxl-to-md

A tool to convert Roblox XML place files to readable Markdown documents.

## Features

- Converts Roblox `.rbxlx` files to a more readable format
- Extracts paths, IDs, classes, and properties
- Supports filters for ignoring specific paths or classes
- Outputs to separate files by high-level path or a single file

## Usage

```bash
./rbxlx-to-md [input_file] [options]
```

### Options

- `--output, -o` - Output directory path (default: input_file_name)
- `--settings, -s` - Path to settings JSON file (default: settings.json)
- `--show-class, -c` - Include class names in the output
- `--single-file, -f` - Output to a single file instead of separate files per path
- `--show-properties, -p` - Include properties in the output (default: True)

### Example

```bash
./rbxlx-to-md game.rbxlx -o game_paths -c
```

## Building From Source

### Prerequisites

- Python 3.6+
- PyInstaller (for creating standalone executables)

### Building Binaries

To build standalone executables for Windows, macOS, and Linux:

1. Make sure the build script is executable:
   ```bash
   chmod +x build.sh
   ```

2. Run the build script:
   ```bash
   ./build.sh
   ```

3. The binaries will be created in the `release` directory, with separate folders for each platform.

## Settings

Create a `settings.json` file to configure filters:

```json
{
  "Ignore": {
    "ClassName": ["Camera", "Terrain"],
    "Path": ["Workspace.Terrain", "Lighting.*"]
  }
}
```

## License

[Insert your license information here] 