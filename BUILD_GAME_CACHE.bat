@echo off
setlocal EnableExtensions
title HL2Quest - Local Steam Cache Builder
echo HL2Quest - Half-Life 2, Episodes, Lost Coast, Portal and Portal 2
echo This helper uses your owned PC game files and the matching release APK.
echo Existing output folders are never replaced.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\build_game_cache.ps1" %*
set "RESULT=%ERRORLEVEL%"
if "%~1"=="" pause
exit /b %RESULT%
