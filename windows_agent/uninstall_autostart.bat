@echo off
echo ================================================
echo TimeTrack Agent - Autostart Deinstallation
echo ================================================
echo.
echo Fuehre PowerShell-Skript aus...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0install_autostart.ps1" -Uninstall

pause
