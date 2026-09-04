# Disinstalla FantAiuto: toglie scorciatoie, aggiornamento automatico, voce in
# "App installate" e infine la cartella del programma.
#
# Chiede prima se vuoi conservare i tuoi dati (rosa segnata, impostazioni).

$ErrorActionPreference = "SilentlyContinue"

$NOME = "FantAiuto"
$cartella = Split-Path -Parent $MyInvocation.MyCommand.Path
$chiave = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$NOME"
$attivita = "FantAiuto - aggiornamento dati"

Write-Host ""
Write-Host "  DISINSTALLAZIONE DI $NOME" -ForegroundColor White
Write-Host "  -------------------------" -ForegroundColor DarkYellow
Write-Host "  Cartella: $cartella"
Write-Host ""
$conferma = Read-Host "  Procedo? (s/n)"
if ($conferma -ne "s" -and $conferma -ne "S") { Write-Host "  Annullato."; exit }

$salva = Read-Host "  Conservo i tuoi dati (rosa e impostazioni) sul Desktop? (s/n)"

# chiudo il programma se e' aperto
Get-CimInstance Win32_Process -Filter "Name like '%python%'" |
    Where-Object { $_.CommandLine -and ($_.CommandLine -like "*avvia.py*" -or $_.CommandLine -like "*streamlit*run*app.py*") } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Sleep -Milliseconds 700

if ($salva -eq "s" -or $salva -eq "S") {
    $backup = Join-Path ([Environment]::GetFolderPath("Desktop")) "FantAiuto - dati salvati"
    New-Item -ItemType Directory -Force -Path $backup | Out-Null
    foreach ($f in @("asta.json", "config.json", "valutazioni.json")) {
        $src = Join-Path $cartella "dati\$f"
        if (Test-Path $src) { Copy-Item $src $backup -Force }
    }
    Write-Host "  Dati salvati in: $backup" -ForegroundColor Green
}

schtasks /Delete /TN "$attivita" /F | Out-Null
Write-Host "  Tolto l'aggiornamento automatico"

$menu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$NOME.lnk"
$desk = Join-Path ([Environment]::GetFolderPath("Desktop")) "$NOME.lnk"
Remove-Item $menu, $desk -Force
Write-Host "  Tolte le scorciatoie"

Remove-Item $chiave -Recurse -Force
Write-Host "  Tolta la voce da App installate"

# non posso cancellare la cartella da cui sto girando: lo faccio fare a un altro
Set-Location $env:TEMP
Start-Process powershell -ArgumentList @(
    "-NoProfile", "-WindowStyle", "Hidden", "-Command",
    "Start-Sleep 2; Remove-Item '$cartella' -Recurse -Force"
)
Write-Host ""
Write-Host "  Fatto. La cartella del programma sparisce tra un paio di secondi." -ForegroundColor Green
Write-Host ""
Read-Host "  Invio per chiudere"
