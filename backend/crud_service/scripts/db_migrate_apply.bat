@echo off
setlocal
set ENVIRONMENT=%1

if "%ENVIRONMENT%"=="" (
    echo Usage: db_migrate_apply.bat [local|develop|staging|production]
    exit /b 1
)

if "%ENVIRONMENT%"=="local"  goto run
if "%ENVIRONMENT%"=="develop" goto run
if "%ENVIRONMENT%"=="staging" goto run
if "%ENVIRONMENT%"=="production" goto run

echo Input env: %ENVIRONMENT% is not supported!
exit /b 1

:run
echo Running alembic upgrade for environment %ENVIRONMENT% ...
cd /d "%~dp0\.."
call alembic upgrade head
if errorlevel 1 (
    echo Migration failed.
    exit /b 1
)
echo Migration completed successfully.
endlocal
