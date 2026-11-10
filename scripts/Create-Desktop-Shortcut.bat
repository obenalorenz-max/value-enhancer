@echo off
setlocal enabledelayedexpansion
title Magpie - Create Desktop Shortcut

echo =======================================================
echo     Magpie FSR Upscaler - Desktop Shortcut Creator
echo =======================================================
echo.

:: 1. Search for Magpie.exe in common locations
set "MAGPIE_PATH="

if exist "%~dp0Magpie.exe" (
    set "MAGPIE_PATH=%~dp0Magpie.exe"
) else if exist "%USERPROFILE%\Downloads\Magpie\Magpie.exe" (
    set "MAGPIE_PATH=%USERPROFILE%\Downloads\Magpie\Magpie.exe"
) else (
    for /d %%D in ("%USERPROFILE%\Downloads\Magpie*") do (
        if exist "%%D\Magpie.exe" set "MAGPIE_PATH=%%D\Magpie.exe"
    )
)

:: 2. If not found automatically, prompt user to drag and drop Magpie.exe
if "%MAGPIE_PATH%"=="" (
    echo [!] Magpie.exe not found automatically in Downloads folder.
    echo.
    echo Please drag and drop your 'Magpie.exe' file into this window and press ENTER:
    set /p "MAGPIE_PATH=> "
    set "MAGPIE_PATH=!MAGPIE_PATH:"=!"
)

if not exist "!MAGPIE_PATH!" (
    echo.
    echo [ERROR] The path "!MAGPIE_PATH!" does not exist.
    pause
    exit /b 1
)

:: 3. Create Windows Desktop Shortcut via PowerShell WScript.Shell
echo.
echo [*] Found Magpie at: "!MAGPIE_PATH!"
echo [*] Creating shortcut on your Windows 11 Desktop...

powershell -NoProfile -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$s = $ws.CreateShortcut([IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'Magpie (FSR Upscaler).lnk')); " ^
  "$s.TargetPath = '!MAGPIE_PATH!'; " ^
  "$s.WorkingDirectory = [IO.Path]::GetDirectoryName('!MAGPIE_PATH!'); " ^
  "$s.Description = 'Magpie Windowed FSR Upscaler for BlueStacks and Games'; " ^
  "$s.Save()"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Shortcut 'Magpie (FSR Upscaler)' created on your Desktop!
    echo Hotkey reminder: Press [Win + Shift + A] while BlueStacks MLBB is open.
) else (
    echo.
    echo [ERROR] Failed to create shortcut.
)

echo.
pause
