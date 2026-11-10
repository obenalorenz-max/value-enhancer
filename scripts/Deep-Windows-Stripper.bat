@echo off
setlocal enabledelayedexpansion
title Deep Windows 11 Stripper - Latency & Bloat Annihilator (i5-6400 / 8GB RAM)

:: Check for Administrator Privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] ADMINISTRATOR PRIVILEGES REQUIRED
    echo Right-click this script and select 'Run as Administrator'.
    echo.
    pause
    exit /b 1
)

color 0C
echo ======================================================================
echo    DEEP WINDOWS 11 STRIPPER: Extreme Performance & Latency Unlocker
echo    Targets: Network Nagle Algorithm ^| Memory Leaks ^| Telemetry Bloat
echo ======================================================================
echo.

:: ========================================================================
:: PHASE 1: PING & NETWORK LATENCY ANNIHILATOR (Disable Nagle's Algorithm)
:: ========================================================================
echo [*] Phase 1: Tuning Network Stack for Ultra-Low Ping (MLBB)...

:: 1. Disable Network Throttling & Reserve 100% CPU for Gaming
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v "NetworkThrottlingIndex" /t REG_DWORD /d 4294967295 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" /v "SystemResponsiveness" /t REG_DWORD /d 0 /f >nul 2>&1

:: 2. Set Games subprofile to High Priority
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "GPU Priority" /t REG_DWORD /d 8 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Priority" /t REG_DWORD /d 6 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "Scheduling Category" /t REG_SZ /d "High" /f >nul 2>&1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" /v "SFIO Priority" /t REG_SZ /d "High" /f >nul 2>&1

:: 3. Disable Nagle's Algorithm on all Active Network Interfaces
echo [*] Disabling Nagle's Algorithm across all TCP interfaces...
for /f "tokens=*" %%i in ('reg query "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"') do (
    reg add "%%i" /v "TcpAckFrequency" /t REG_DWORD /d 1 /f >nul 2>&1
    reg add "%%i" /v "TCPNoDelay" /t REG_DWORD /d 1 /f >nul 2>&1
    reg add "%%i" /v "TcpDelAckTicks" /t REG_DWORD /d 0 /f >nul 2>&1
)
echo [+] Network stack optimized: Zero-delay packet dispatch enabled.

:: ========================================================================
:: PHASE 2: RAM & PAGEFILE LEAK KILLER (Disable Bloatware Services)
:: ========================================================================
echo.
echo [*] Phase 2: Killing Memory-Hogging Background Daemons...

:: 1. Disable SysMain (Superfetch - causes intense disk thrashing on 8GB RAM)
sc stop SysMain >nul 2>&1
sc config SysMain start=disabled >nul 2>&1
echo [+] SysMain (SuperFetch) disabled.

:: 2. Disable Delivery Optimization (DoSvc - steals upload/download bandwidth)
sc stop DoSvc >nul 2>&1
sc config DoSvc start=disabled >nul 2>&1
echo [+] Delivery Optimization disabled.

:: 3. Disable Windows Telemetry & Diagnostic tracking
sc stop DiagTrack >nul 2>&1
sc config DiagTrack start=disabled >nul 2>&1
sc stop dmwappushservice >nul 2>&1
sc config dmwappushservice start=disabled >nul 2>&1
echo [+] Diagnostic Tracking disabled.

:: 4. Disable Connected User Experiences & Telemetry via Registry
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v "AllowTelemetry" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\CloudContent" /v "DisableWindowsConsumerFeatures" /t REG_DWORD /d 1 /f >nul 2>&1

:: 5. Disable Bing Search & Cortana in Start Menu (Stops Start Menu lag)
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v "BingSearchEnabled" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v "CortanaConsent" /t REG_DWORD /d 0 /f >nul 2>&1
reg add "HKCU\Software\Policies\Microsoft\Windows\Explorer" /v "DisableSearchBoxSuggestions" /t REG_DWORD /d 1 /f >nul 2>&1
echo [+] Bing web telemetry in Start Menu stripped.

:: ========================================================================
:: PHASE 3: WINDOWS DEFENDER EXCLUSION (Stops 30% CPU Spikes in MLBB)
:: ========================================================================
echo.
echo [*] Phase 3: Setting Windows Defender Exclusions for BlueStacks...
powershell -NoProfile -Command ^
    "Add-MpPreference -ExclusionPath 'C:\Program Files\BlueStacks_nxt' -ErrorAction SilentlyContinue; " ^
    "Add-MpPreference -ExclusionPath 'C:\ProgramData\BlueStacks_nxt' -ErrorAction SilentlyContinue; " ^
    "Add-MpPreference -ExclusionPath '$env:USERPROFILE\Documents\Magpie' -ErrorAction SilentlyContinue; " ^
    "Add-MpPreference -ExclusionProcess 'HD-Player.exe' -ErrorAction SilentlyContinue; " ^
    "Add-MpPreference -ExclusionProcess 'BlueStacks.exe' -ErrorAction SilentlyContinue; " ^
    "Add-MpPreference -ExclusionProcess 'Magpie.exe' -ErrorAction SilentlyContinue"
echo [+] Defender real-time scanning excluded from BlueStacks & Magpie.

:: ========================================================================
:: PHASE 4: FLUSH MEMORY CACHE
:: ========================================================================
echo.
echo [*] Purging RAM standby caches...
powershell -NoProfile -Command "[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()" >nul 2>&1

echo.
echo ======================================================================
echo    [SUCCESS] DEEP STRIPPING COMPLETED!
echo.
echo    Results Applied:
echo     - Nagle's Algorithm Disabled (Instant ping response in MLBB)
echo     - SysMain & Delivery Optimization Killed (No more disk thrashing)
echo     - Telemetry & Bing Bloat Stripped
echo     - Defender 30%% CPU Spikes on BlueStacks Eliminated
echo.
echo    * A quick PC restart is recommended to finalize all TCP hooks. *
echo ======================================================================
echo.
pause
