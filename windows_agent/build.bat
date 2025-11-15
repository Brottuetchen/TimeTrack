@echo off
echo ================================================
echo TimeTrack Agent - Build Script
echo ================================================
echo.

REM Prüfe ob PyInstaller installiert ist
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller ist nicht installiert. Installiere jetzt...
    pip install pyinstaller
)

REM Lösche alte Build-Artefakte
echo Loesche alte Build-Dateien...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist TimeTrackAgent.exe del TimeTrackAgent.exe

REM Erstelle EXE mit PyInstaller
echo.
echo Erstelle EXE mit PyInstaller...
pyinstaller --clean timetrack_agent.spec

REM Kopiere EXE ins Hauptverzeichnis
if exist dist\TimeTrackAgent.exe (
    echo.
    echo Kopiere EXE...
    copy dist\TimeTrackAgent.exe TimeTrackAgent.exe
    echo.
    echo ================================================
    echo Build erfolgreich!
    echo ================================================
    echo EXE erstellt: TimeTrackAgent.exe
    echo.
    echo WICHTIG: Stelle sicher, dass config.json im selben
    echo          Verzeichnis wie die EXE liegt!
    echo.
) else (
    echo.
    echo ================================================
    echo Build fehlgeschlagen!
    echo ================================================
    exit /b 1
)

pause
