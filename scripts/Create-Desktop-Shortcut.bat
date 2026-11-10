@echo off
setlocal enabledelayedexpansion
title Magpie FSR Upscaler - Auto Setup & Shortcut Creator

echo ======================================================================
echo       Magpie FSR Upscaler - Auto Installer & Shortcut Creator
echo       Destination: %USERPROFILE%\Documents\Magpie
echo ======================================================================
echo.

set "TARGET_DIR=%USERPROFILE%\Documents\Magpie"
set "EXE_PATH=%TARGET_DIR%\Magpie.exe"
set "ZIP_PATH=%TARGET_DIR%\Magpie.zip"
set "DOWNLOAD_URL=https://github.com/Blinue/Magpie/releases/download/v0.13.0/Magpie-v0.13.0-x64.zip"

if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

:: Check if Magpie.exe already exists
if not exist "%EXE_PATH%" (
    echo [*] Magpie not found locally.
    echo [*] Downloading Magpie-v0.13.0-x64 from GitHub directly to:
    echo     %TARGET_DIR%
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
        "Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%ZIP_PATH%'; " ^
        "Expand-Archive -Path '%ZIP_PATH%' -DestinationPath '%TARGET_DIR%' -Force; " ^
        "Remove-Item -Force '%ZIP_PATH%'"
)

if not exist "%EXE_PATH%" (
    :: In case files extracted into a subfolder
    for /r "%TARGET_DIR%" %%F in (Magpie.exe) do (
        if exist "%%F" set "EXE_PATH=%%F"
    )
)

if not exist "%EXE_PATH%" (
    echo [ERROR] Failed to locate Magpie.exe. Please check internet connection.
    pause
    exit /b 1
)

echo.
echo [*] Magpie located at: "%EXE_PATH%"
echo [*] Creating shortcuts on Desktop and Documents...

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$desk = [Environment]::GetFolderPath('Desktop'); " ^
  "$doc = [Environment]::GetFolderPath('MyDocuments'); " ^
  "$s1 = $ws.CreateShortcut([IO.Path]::Combine($desk, 'Magpie (FSR Upscaler).lnk')); " ^
  "$s1.TargetPath = '!EXE_PATH!'; " ^
  "$s1.WorkingDirectory = [IO.Path]::GetDirectoryName('!EXE_PATH!'); " ^
  "$s1.Description = 'Magpie Windowed FSR Upscaler for BlueStacks MLBB'; " ^
  "$s1.Save(); " ^
  "$s2 = $ws.CreateShortcut([IO.Path]::Combine($doc, 'Magpie (FSR Upscaler).lnk')); " ^
  "$s2.TargetPath = '!EXE_PATH!'; " ^
  "$s2.WorkingDirectory = [IO.Path]::GetDirectoryName('!EXE_PATH!'); " ^
  "$s2.Description = 'Magpie Windowed FSR Upscaler for BlueStacks MLBB'; " ^
  "$s2.Save();"

echo.
echo ======================================================================
echo  [SUCCESS] Magpie Shortcuts Created:
echo    1. %USERPROFILE%\Desktop\Magpie (FSR Upscaler).lnk
echo    2. %USERPROFILE%\Documents\Magpie (FSR Upscaler).lnk
echo.
echo  Installed Path: %EXE_PATH%
echo.
echo  Hotkey Reminder: Press [Win + Shift + A] while MLBB is active!
echo ======================================================================
echo.
pause
