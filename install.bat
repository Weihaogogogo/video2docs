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
        winget install ffmpeg
    ) else (
        echo [ERROR] winget not found. Please install ffmpeg manually:
        echo   Run: winget install ffmpeg
        exit /b 1
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
