# TimeTrack Agent - Autostart Installation
# Dieses Skript erstellt eine Verknüpfung im Windows Autostart-Ordner

param(
    [switch]$Uninstall
)

$AppName = "TimeTrackAgent"
$ExeName = "TimeTrackAgent.exe"
$CurrentDir = $PSScriptRoot
$ExePath = Join-Path $CurrentDir $ExeName
$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupFolder "$AppName.lnk"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "TimeTrack Agent - Autostart Installation" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

if ($Uninstall) {
    # Deinstallation
    if (Test-Path $ShortcutPath) {
        Remove-Item $ShortcutPath -Force
        Write-Host "✓ Autostart-Verknüpfung entfernt" -ForegroundColor Green
        Write-Host "  Pfad: $ShortcutPath" -ForegroundColor Gray
    } else {
        Write-Host "✗ Keine Autostart-Verknüpfung gefunden" -ForegroundColor Yellow
    }
    Write-Host ""
    exit 0
}

# Installation
# Prüfe ob EXE existiert
if (-not (Test-Path $ExePath)) {
    Write-Host "✗ FEHLER: $ExeName nicht gefunden!" -ForegroundColor Red
    Write-Host "  Erwartet in: $ExePath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Bitte führe zuerst 'build.bat' aus, um die EXE zu erstellen." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Prüfe ob config.json existiert
$ConfigPath = Join-Path $CurrentDir "config.json"
if (-not (Test-Path $ConfigPath)) {
    Write-Host "⚠ WARNUNG: config.json nicht gefunden!" -ForegroundColor Yellow
    Write-Host "  Bitte erstelle die config.json bevor du die Anwendung startest." -ForegroundColor Yellow
    Write-Host ""
}

# Erstelle Verknüpfung
try {
    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $ExePath
    $Shortcut.WorkingDirectory = $CurrentDir
    $Shortcut.Description = "TimeTrack Activity Tracking Agent"
    $Shortcut.Save()

    Write-Host "✓ Autostart erfolgreich eingerichtet!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Details:" -ForegroundColor Cyan
    Write-Host "  Verknüpfung: $ShortcutPath" -ForegroundColor Gray
    Write-Host "  Ziel:        $ExePath" -ForegroundColor Gray
    Write-Host "  Arbeitsdir:  $CurrentDir" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Der TimeTrack Agent wird nun bei jedem Windows-Start automatisch gestartet." -ForegroundColor Green
    Write-Host ""
    Write-Host "Hinweise:" -ForegroundColor Cyan
    Write-Host "  - config.json muss im selben Verzeichnis wie die EXE liegen" -ForegroundColor Gray
    Write-Host "  - Zum Entfernen: .\install_autostart.ps1 -Uninstall" -ForegroundColor Gray
    Write-Host "  - Manueller Zugriff: Win+R -> shell:startup" -ForegroundColor Gray
    Write-Host ""

} catch {
    Write-Host "✗ FEHLER beim Erstellen der Verknüpfung:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    exit 1
}
