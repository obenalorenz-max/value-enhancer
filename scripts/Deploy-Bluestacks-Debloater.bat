@echo off
setlocal enabledelayedexpansion
title BlueStacks 5 Debloater & MLBB Performance Accelerator

echo ======================================================================
echo    BlueStacks 5 Debloater - Remove Ads, Telemetry & Background Bloat
echo    Source: Jordan231111/Bluestacks-Debloat (Latest 2026 Release)
echo ======================================================================
echo.

set "TARGET_DIR=%USERPROFILE%\Documents\BluestacksDebloat"
set "EXE_PATH=%TARGET_DIR%\BluestacksDebloat.exe"
set "DOWNLOAD_URL=https://github.com/Jordan231111/Bluestacks-Debloat/releases/latest/download/BluestacksDebloat.exe"

if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

:: 1. Download BluestacksDebloat.exe if not already present
if not exist "%EXE_PATH%" (
    echo [*] Downloading latest BluestacksDebloat.exe from GitHub...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
        "Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%EXE_PATH%'"
)

if not exist "%EXE_PATH%" (
    echo [ERROR] Failed to download BluestacksDebloat.exe. Check your internet connection.
    pause
    exit /b 1
)

echo [+] BluestacksDebloat.exe ready at: "%EXE_PATH%"

:: 2. Create Desktop and Documents shortcuts
echo [*] Creating shortcuts on Desktop and Documents...
powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$desk = [Environment]::GetFolderPath('Desktop'); " ^
  "$doc = [Environment]::GetFolderPath('MyDocuments'); " ^
  "$s1 = $ws.CreateShortcut([IO.Path]::Combine($desk, 'BlueStacks Debloater.lnk')); " ^
  "$s1.TargetPath = '!EXE_PATH!'; " ^
  "$s1.WorkingDirectory = '!TARGET_DIR!'; " ^
  "$s1.Description = 'Debloat BlueStacks 5 remove ads and telemetry'; " ^
  "$s1.Save(); " ^
  "$s2 = $ws.CreateShortcut([IO.Path]::Combine($doc, 'BlueStacks Debloater.lnk')); " ^
  "$s2.TargetPath = '!EXE_PATH!'; " ^
  "$s2.WorkingDirectory = '!TARGET_DIR!'; " ^
  "$s2.Description = 'Debloat BlueStacks 5 remove ads and telemetry'; " ^
  "$s2.Save();"

echo.
echo ======================================================================
echo  [SUCCESS] BlueStacks Debloater Installed!
echo.
echo  RECOMMENDED SETTINGS IN DEBLOATER APP:
echo  1. Select your BlueStacks instance(s)
echo  2. Click 'Maximum Debloat' or check:
echo     - Disable ads & sponsored games
echo     - Remove BlueStacks X / Cloud Services
echo     - Block telemetry & tracking domains
echo  3. Click 'Apply' (It will auto-restart BlueStacks clean & fast!)
echo ======================================================================
echo.
echo Launching BlueStacks Debloater now...
start "" "%EXE_PATH%"
pause
