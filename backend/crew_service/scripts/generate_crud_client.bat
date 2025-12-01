@echo off
setlocal enabledelayedexpansion

echo Generating CRUD service API client...

REM Resolve directories
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Determine OpenAPI URL
if defined CRUD_SERVICE_OPENAPI_URL (
    set "OPENAPI_URL=%CRUD_SERVICE_OPENAPI_URL%"
) else (
    set "OPENAPI_URL=http://localhost:8000/openapi.json"
)

set "OUTPUT_DIR=%PROJECT_ROOT%\app\api"
set "CLIENT_DIR=%OUTPUT_DIR%\crud_client"

echo OpenAPI URL:      %OPENAPI_URL%
echo Output directory: %CLIENT_DIR%

REM Check if openapi-python-client exists
python -c "import openapi_python_client" >nul 2>&1
if errorlevel 1 (
    echo Installing openapi-python-client==2.11.0...
    python -m pip install openapi-python-client==2.11.0
)

REM Create directories safely
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Generate client
openapi-python-client generate ^
    --url "%OPENAPI_URL%" ^
    --output-path "%CLIENT_DIR%" ^
    --meta none ^
    --overwrite

echo Client generated successfully at %CLIENT_DIR%
pause
