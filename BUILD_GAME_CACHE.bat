@echo off
setlocal EnableExtensions
title Half-Life 2 VR Standalone 0.982 - HL2, Lost Coast and Episodes Cache Builder

echo ============================================================
echo   Half-Life 2 VR Standalone 0.982 - HL2 + Lost Coast + Episodes Cache
echo ============================================================
echo.
echo This tool uses your legally installed Half-Life 2 files.
echo Commercial game data is not included in this release.
echo.

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\build_game_cache.ps1"
set "RESULT=%ERRORLEVEL%"

echo.
if "%RESULT%"=="0" (
    echo Cache build completed successfully.
    echo Result: "%~dp0game_cache\srceng"
) else (
    echo Cache build failed. Error code: %RESULT%
)
echo.
pause
exit /b %RESULT%
