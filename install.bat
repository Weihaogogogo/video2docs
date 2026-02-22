@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    Video2Docs Installer (Windows)
echo ========================================

echo.
echo [0/4] Checking ffmpeg...

where ffmpeg >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] ffmpeg is installed
) else (
    echo [INFO] ffmpeg not found, trying to install...
    where winget >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] winget found, installing ffmpeg...
        winget install ffmpeg
    ) else (
        echo [INFO] winget not found, installing ffmpeg via PowerShell...

        :: Check if git-bash or wget available (comes with git for Windows)
        where git >nul 2>&1
        if %errorlevel% equ 0 (
            :: Use git-bash to download ffmpeg
            git bash -c "curl -L https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip -o ffmpeg.zip"
        ) else (
            :: Use PowerShell to download
            powershell -Command "Invoke-WebRequest -Uri 'https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip' -OutFile 'ffmpeg.zip'"
        )

        if not exist ffmpeg.zip (
            echo [ERROR] Failed to download ffmpeg. Please install manually from:
            echo   https://ffmpeg.org/download.html
            exit /b 1
        )

        echo Extracting ffmpeg...
        powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'C:\ffmpeg-temp' -Force"

        :: Create ffmpeg directory in Program Files
        if not exist "C:\ffmpeg" mkdir "C:\ffmpeg"
        xcopy /E /Y "C:\ffmpeg-temp\ffmpeg-7.1-essentials_build\*" "C:\ffmpeg\"

        :: Add to PATH
        setx PATH "%PATH%;C:\ffmpeg\bin" >nul

        :: Cleanup
        rmdir /S /Q C:\ffmpeg-temp
        del ffmpeg.zip

        echo [OK] ffmpeg installed to C:\ffmpeg\bin
        echo [INFO] Please restart your terminal to use ffmpeg
    )
)

echo.
echo [1/4] Checking venv...

if exist "venv\Scripts\activate.bat" (
    echo [INFO] venv already exists, skipping creation
) else (
    echo [1/4] Creating venv...
    python -m venv venv
    echo [OK] venv created
)

echo.
echo [2/4] Installing Python dependencies...

echo.
echo Upgrading pip...
call venv\Scripts\pip.exe install --upgrade pip

echo.
echo Installing requirements...
call venv\Scripts\pip.exe install -r requirements.txt

echo.
echo [OK] Dependencies installed

echo.
echo [3/4] Verifying Python dependencies...
call venv\Scripts\python.exe -c "import typer, rich, ytdlp, ffmpeg, openai, jinja2, dotenv, pydantic_settings, faster_whisper, weasyprint, markdown" 2>nul
if %errorlevel% equ 0 (
    echo [OK] Python dependencies verified
) else (
    echo [WARNING] Some dependencies failed to verify
)

echo.
echo [4/4] Verifying ffmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] ffmpeg verified
) else (
    echo [WARNING] ffmpeg verification failed
)

echo.
echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo Usage:
echo 1. Create .env file with your API credentials
echo 2. Run: venv\Scripts\activate.bat
echo 3. Run: python -m video2docs
echo.
