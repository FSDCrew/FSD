@echo off
setlocal enabledelayedexpansion
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=crud
set DB_USER=crew
set DB_PASSWORD=postgres
set DB_DOCKER_NAME=postgres-crew-crud
set PG_IMAGE=postgres:15.1

REM Project root = two levels up from this script
for %%I in ("%~dp0") do set SCRIPT_DIR=%%~fI
cd /d "%SCRIPT_DIR%\..\.."
set PROJECT_ROOT=%CD%
set DATA_DIR=%PROJECT_ROOT%\.data\postgresql\crud

echo Creating data dir: %DATA_DIR%
mkdir "%DATA_DIR%" 2>nul

echo Stopping/removing existing container (if any)...
docker rm -f "%DB_DOCKER_NAME%" >nul 2>nul

echo Starting PostgreSQL container '%DB_DOCKER_NAME%'...
docker run --name "%DB_DOCKER_NAME%" ^
  -e POSTGRES_USER=%DB_USER% ^
  -e POSTGRES_PASSWORD=%DB_PASSWORD% ^
  -e POSTGRES_DB=%DB_NAME% ^
  -e PGDATA=/var/lib/postgresql/data/pgdata ^
  -p %DB_PORT%:5432 ^
  -v "%DATA_DIR%:/var/lib/postgresql/data" ^
  -d "%PG_IMAGE%"

echo.
echo Container started. Last lines of logs:
docker logs --tail 20 "%DB_DOCKER_NAME%"

echo.
echo Postgres should be available at:
echo   host=%DB_HOST%  port=%DB_PORT%  db=%DB_NAME%  user=%DB_USER%
echo.
echo SQLAlchemy URL (sync):
echo   postgresql+psycopg://%DB_USER%:%DB_PASSWORD%@%DB_HOST%:%DB_PORT%/%DB_NAME%
echo SQLAlchemy URL (async):
echo   postgresql+asyncpg://%DB_USER%:%DB_PASSWORD%@%DB_HOST%:%DB_PORT%/%DB_NAME%
echo.
echo Tip: if connection fails immediately, wait a few seconds or run:
echo   docker logs -f %DB_DOCKER_NAME%
endlocal
