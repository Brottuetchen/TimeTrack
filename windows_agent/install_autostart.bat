@echo off
echo ================================================
echo TimeTrack Agent - Autostart Installation
echo ================================================
echo.
echo Fuehre PowerShell-Skript aus...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0install_autostart.ps1"

if errorlevel 1 (
    echo.
    echo Installation fehlgeschlagen!
    pause
    exit /b 1
)

pause
