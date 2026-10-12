@echo off
setlocal EnableExtensions
title MaxKB Course Demo Launcher

set "DOCKER_EXE=D:\DockerDesktop\app\Docker Desktop.exe"
set "DEMO_URL=http://localhost:8080/chat/26724dec603349ef/"

if not exist "%DOCKER_EXE%" (
  echo [ERROR] Docker Desktop was not found at:
  echo %DOCKER_EXE%
  pause
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo [1/4] Starting Docker Desktop with a clean runtime directory on D drive...
  taskkill /IM "Docker Desktop.exe" /T /F >nul 2>&1
  taskkill /IM "com.docker.backend.exe" /T /F >nul 2>&1
  wsl.exe --shutdown >nul 2>&1

  set "LOCALAPPDATA=D:\DockerDesktop\runtime\session-%RANDOM%-%RANDOM%"
  if not exist "%LOCALAPPDATA%" mkdir "%LOCALAPPDATA%"
  start "" /min "%DOCKER_EXE%"

  for /L %%I in (1,1,60) do (
    docker info >nul 2>&1
    if not errorlevel 1 goto docker_ready
    ping 127.0.0.1 -n 3 >nul
  )

  echo [ERROR] Docker Desktop did not become ready within 120 seconds.
  echo Please open Docker Desktop to view the error message.
  pause
  exit /b 1
)

:docker_ready
echo [2/4] Docker Desktop is ready.
echo [3/4] Starting MaxKB and the after-sales MCP service...
docker start maxkb-course maxkb-smart-tools >nul

for /L %%I in (1,1,60) do (
  curl.exe --max-time 2 -s -f "http://localhost:8080/" >nul 2>&1
  if not errorlevel 1 goto web_ready
  ping 127.0.0.1 -n 3 >nul
)

echo [ERROR] MaxKB did not become ready within 120 seconds.
pause
exit /b 1

:web_ready
echo [4/4] Opening the course demo...
start "" "%DEMO_URL%"
echo.
echo MaxKB and the MCP service are running.
echo You can close this window now.
ping 127.0.0.1 -n 6 >nul
endlocal
