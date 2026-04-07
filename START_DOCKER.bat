@echo off
echo.
echo ========================================
echo   OpsPilot++ - Docker Startup Helper
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed!
    echo.
    echo Please download and install Docker Desktop:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

echo ✅ Docker is installed
echo.

REM Check if Docker daemon is running
echo Checking if Docker daemon is running...
docker ps >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker daemon is not running!
    echo.
    echo Starting Docker Desktop...
    echo Please wait for Docker to fully initialize...
    echo.
    
    REM Try to start Docker Desktop
    if exist "C:\Program Files\Docker\Docker\Docker.exe" (
        start "" "C:\Program Files\Docker\Docker\Docker.exe"
    ) else if exist "C:\Program Files (x86)\Docker\Docker\Docker.exe" (
        start "" "C:\Program Files (x86)\Docker\Docker\Docker.exe"
    ) else (
        echo Could not find Docker Desktop installation
        echo Please start Docker Desktop manually from Start menu
        pause
        exit /b 1
    )
    
    echo.
    echo Waiting for Docker to start (this may take 30-60 seconds)...
    timeout /t 10 /nobreak
    
    REM Check again
    docker ps >nul 2>&1
    if errorlevel 1 (
        echo.
        echo ⏳ Docker is still starting...
        echo Please wait a bit longer and try again
        pause
        exit /b 1
    )
)

echo ✅ Docker daemon is running!
echo.
echo ========================================
echo   Docker is ready!
echo ========================================
echo.
echo You can now run: python main.py
echo.
pause
