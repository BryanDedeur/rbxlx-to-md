#!/bin/bash

# Exit on error
set -e

echo "🚀 Building rbxlx-to-md executables for multiple platforms"

# Create release directory if it doesn't exist
mkdir -p release

# Check if PyInstaller is installed, install if not
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip3 install pyinstaller
fi

# Function to build for a specific platform
build_for_platform() {
    platform=$1
    echo "🔨 Building for $platform..."
    
    # Create platform-specific folder
    mkdir -p "release/$platform"
    
    # Platform-specific settings
    case $platform in
        windows)
            output_name="rbxlx-to-md.exe"
            pyinstaller_opts="--onefile --windowed"
            ;;
        macos)
            output_name="rbxlx-to-md"
            pyinstaller_opts="--onefile"
            ;;
        linux)
            output_name="rbxlx-to-md"
            pyinstaller_opts="--onefile"
            ;;
    esac
    
    # Run PyInstaller
    if [ "$platform" = "windows" ] && [ "$(uname)" != "MINGW"* ] && [ "$(uname)" != "MSYS"* ] && [ "$(uname)" != "CYGWIN"* ]; then
        echo "⚠️  Building Windows executable requires Windows or Wine environment"
        echo "⚠️  Skipping Windows build as this appears to be a $(uname) environment"
    else
        python3 -m PyInstaller $pyinstaller_opts --name "$output_name" src/rbxlx-to-md.py
        
        # Copy executable to release folder
        cp dist/$output_name "release/$platform/"
        
        # Copy settings.json template if it exists
        if [ -f "settings.json" ]; then
            cp settings.json "release/$platform/"
        else
            # Create a minimal settings.json template
            cat > "release/$platform/settings.json" << EOL
{
  "Ignore": {
    "ClassName": [],
    "Path": []
  }
}
EOL
        fi
        
        # Add README for this platform
        cat > "release/$platform/README.txt" << EOL
rbxlx-to-md for $platform

Usage:
$([ "$platform" = "windows" ] && echo ".\\rbxlx-to-md.exe" || echo "./rbxlx-to-md") [input_file] [options]

Options:
  --output, -o      Output directory path (default: input_file_name)
  --settings, -s    Path to settings JSON file (default: settings.json)
  --show-class, -c  Include class names in the output
  --single-file, -f Output to a single file instead of separate files per path
  --show-properties, -p Include properties in the output (default: True)

Example:
$([ "$platform" = "windows" ] && echo ".\\rbxlx-to-md.exe" || echo "./rbxlx-to-md") game.rbxlx -o game_paths -c

For more information, visit: https://github.com/bdedeurwaerder/rbxl-to-md
EOL
    fi
    
    # Clean up PyInstaller artifacts
    rm -rf build dist *.spec
}

# Build for each platform
build_for_platform "macos"
build_for_platform "linux"
build_for_platform "windows"

echo "📦 Creating release ZIP files..."
cd release

# Create zip for each platform
for platform in */; do
    platform=${platform%/}
    zip -r "rbxlx-to-md-$platform.zip" "$platform"
    echo "✅ Created release/rbxlx-to-md-$platform.zip"
done

cd ..

echo "🎉 All builds completed successfully!"
echo "📋 Release files available in the 'release' directory" 