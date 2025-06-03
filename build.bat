@echo off
setlocal enabledelayedexpansion

echo 🚀 Building rbxlx-to-md executables for multiple platforms

:: Create release directory if it doesn't exist
if not exist release mkdir release

:: Check if PyInstaller is installed, install if not
python -c "import PyInstaller" 2>nul
if %ERRORLEVEL% neq 0 (
    echo 📦 Installing PyInstaller...
    pip install pyinstaller
)

:: Function to build for a specific platform
call :build_for_platform windows

echo 🔨 Cleaning up build artifacts...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del *.spec 2>nul

echo 📦 Creating release ZIP files...
cd release

:: Create zip for each platform using PowerShell
for /d %%p in (*) do (
    echo Creating zip for %%p...
    powershell -command "Compress-Archive -Path '%%p' -DestinationPath 'rbxlx-to-md-%%p.zip' -Force"
    echo ✅ Created release/rbxlx-to-md-%%p.zip
)

cd ..

echo 🎉 All builds completed successfully!
echo 📋 Release files available in the 'release' directory
goto :eof

:build_for_platform
set platform=%~1
echo 🔨 Building for %platform%...

:: Create platform-specific folder
if not exist "release\%platform%" mkdir "release\%platform%"

:: Platform-specific settings
if "%platform%"=="windows" (
    set output_name=rbxlx-to-md.exe
    set pyinstaller_opts=--onefile
) else if "%platform%"=="macos" (
    set output_name=rbxlx-to-md
    set pyinstaller_opts=--onefile
) else if "%platform%"=="linux" (
    set output_name=rbxlx-to-md
    set pyinstaller_opts=--onefile
)

:: Skip non-Windows builds if needed
if not "%platform%"=="windows" (
    echo ⚠️ Building non-Windows executables might require specific environments
    echo ⚠️ Attempting to build %platform% on Windows, but this may not work correctly
)

:: Run PyInstaller
echo Running PyInstaller for %platform%...
python -m PyInstaller %pyinstaller_opts% --name "%output_name%" src/rbxlx-to-md.py

:: Check if PyInstaller succeeded
if not exist "dist\%output_name%" (
    echo ❌ Error: PyInstaller failed to create executable for %platform%
    exit /b 1
)

:: Copy executable to release folder
echo Copying executable to release folder...
copy "dist\%output_name%" "release\%platform%\"
if %ERRORLEVEL% neq 0 (
    echo ❌ Error: Failed to copy executable for %platform%
    exit /b 1
)
echo ✅ Successfully created executable for %platform%

:: Copy rbxlx-to-md-settings template if it exists
if exist "src\rbxlx-to-md-settings.json" (
    copy "src\rbxlx-to-md-settings.json" "release\%platform%\rbxlx-to-md-settings.json"
) else (
    :: Create a minimal rbxlx-to-md-settings template
    echo {> "release\%platform%\rbxlx-to-md-settings.json"
    echo   "Ignore": {>> "release\%platform%\rbxlx-to-md-settings.json"
    echo     "ClassName": [],>> "release\%platform%\rbxlx-to-md-settings.json"
    echo     "Path": []>> "release\%platform%\rbxlx-to-md-settings.json"
    echo   }>> "release\%platform%\rbxlx-to-md-settings.json"
    echo }>> "release\%platform%\rbxlx-to-md-settings.json"
)

:: Add README for this platform
echo rbxlx-to-md for %platform%> "release\%platform%\README.txt"
echo.>> "release\%platform%\README.txt"
echo Usage:>> "release\%platform%\README.txt"
if "%platform%"=="windows" (
    echo .\rbxlx-to-md.exe [input_file] [options]>> "release\%platform%\README.txt"
) else (
    echo ./rbxlx-to-md [input_file] [options]>> "release\%platform%\README.txt"
)
echo.>> "release\%platform%\README.txt"
echo Options:>> "release\%platform%\README.txt"
echo   --output, -o      Output directory path (default: input_file_name)>> "release\%platform%\README.txt"
echo   --settings, -s    Path to settings file (default: rbxlx-to-md-settings)>> "release\%platform%\README.txt"
echo   --show-class, -c  Include class names in the output>> "release\%platform%\README.txt"
echo   --single-file, -f Output to a single file instead of separate files per path>> "release\%platform%\README.txt"
echo   --show-properties, -p Include properties in the output (default: True)>> "release\%platform%\README.txt"
echo.>> "release\%platform%\README.txt"
echo Example:>> "release\%platform%\README.txt"
if "%platform%"=="windows" (
    echo .\rbxlx-to-md.exe game.rbxlx -o game_paths -c>> "release\%platform%\README.txt"
) else (
    echo ./rbxlx-to-md game.rbxlx -o game_paths -c>> "release\%platform%\README.txt"
)
echo.>> "release\%platform%\README.txt"

exit /b 0 