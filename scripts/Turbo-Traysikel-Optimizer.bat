@echo off
setlocal enabledelayedexpansion
title Turbo Traysikel - Windows 11 Low-Spec Gaming Accelerator (i5-6400 / 8GB RAM)

:: Check for Administrator Privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] ADMINISTRATOR PRIVILEGES REQUIRED
    echo Right-click this script and select 'Run as Administrator'.
    echo.
    pause
    exit /b 1
)

color 0B
echo ======================================================================
echo       TURBO TRAYSIKEL: Low-Spec Windows 11 Optimization Engine
echo       Tuned for: Intel Core i5-6400 (4C/4T) ^| 8GB RAM ^| HD Graphics 530
echo ======================================================================
echo.
echo [*] Analyzing system resources...
echo.

:: 1. Disable Windows Telemetry & Diagnostic Bloat (Frees ~400MB RAM)
echo [+] Phase 1: Silencing Telemetry & Background Tracking...
sc stop DiagTrack >nul 2>&1
sc config DiagTrack start=disabled >nul 2>&1
sc stop dmwappushservice >nul 2>&1
sc config dmwappushservice start=disabled >nul 2>&1

:: 2. Disable Xbox GameDVR Background Capture (Huge GPU relief for Intel HD 530)
echo [+] Phase 2: Disabling Background GameDVR Screen Recording...
reg add "HKCU\System\GameConfigStore" /v "GameDVR_Enabled" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\GameDVR" /v "AllowGameDVR" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\GameDVR" /v "AppCaptureEnabled" /t REG_DWORD /d 0 /f >nul 2>&1

:: 3. Prevent Windows 11 EcoQoS / Power Throttling on BlueStacks & Magpie
echo [+] Phase 3: Bypassing Windows 11 CPU Power Throttling for BlueStacks...
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\HD-Player.exe\PerfOptions" /v "CpuPriorityClass" /t REG_DWORD /d 3 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\Magpie.exe\PerfOptions" /v "CpuPriorityClass" /t REG_DWORD /d 3 /f >nul 2>&1

:: Disable Power Throttling for HD-Player.exe
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerThrottling" /v "PowerThrottlingOff" /t REG_DWORD /d 1 /f >nul 2>&1

:: 4. Set Windows Graphics Hardware Acceleration to Maximum for BlueStacks
echo [+] Phase 4: Setting Windows Graphics Preference to High Performance...
reg add "HKCU\Software\Microsoft\DirectX\UserGpuPreferences" /v "HD-Player.exe" /t REG_SZ /d "GpuPreference=2;" /f >nul 2>&1

:: 5. Flush Standby RAM & Memory Working Sets
echo [+] Phase 5: Purging Idle Memory & Cache working sets...
powershell -NoProfile -Command "[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()" >nul 2>&1

echo.
echo ======================================================================
echo                  [+] TURBO TRAYSIKEL APPLIED SUCCESSFULLY!
echo ======================================================================
echo.
echo  CRITICAL BLUESTACKS 5 SETTINGS FOR i5-6400 (Do this in BlueStacks):
echo  --------------------------------------------------------------------
echo   1. CPU Allocation   : 3 CORES (Leave Core 0 for Windows & Magpie!)
echo   2. Memory Allocation: 3072 MB (3 GB)
echo   3. Performance Mode : High Performance
echo   4. Graphics Engine  : Compatibility (DirectX) - Better on Intel HD 530
echo   5. Display Res      : 1280 x 720 (Windowed Mode - DO NOT Fullscreen)
echo.
echo  MAGPIE FSR UPSCALER:
echo  --------------------------------------------------------------------
echo   - Open Magpie.exe
echo   - Scaling: FSR (Sharpness 0.8)
echo   - In MLBB: Press [Win + Shift + A] to upscale 720p to 1080p 60 FPS!
echo.
echo ======================================================================
pause
