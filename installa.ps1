# Installa FantAiuto come programma dell'utente.
#
# Sposta la cartella in %LOCALAPPDATA%\Programs\FantAiuto (la posizione standard per
# i programmi che non richiedono l'amministratore), crea la scorciatoia nel menu Start
# e sul Desktop, aggiorna l'aggiornamento automatico e registra la voce in
# "App installate" di Windows, cosi' si disinstalla come qualsiasi altro programma.
#
# Uso: tasto destro sul file -> "Esegui con PowerShell"

$ErrorActionPreference = "Stop"

$NOME = "FantAiuto"
$origine = Split-Path -Parent $MyInvocation.MyCommand.Path
$destinazione = Join-Path $env:LOCALAPPDATA "Programs\$NOME"
$chiave = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$NOME"
$attivita = "FantAiuto - aggiornamento dati"

function Passo($testo) { Write-Host ("  " + $testo) -ForegroundColor DarkGray }

Write-Host ""
Write-Host "  INSTALLAZIONE DI $NOME" -ForegroundColor White
Write-Host "  ----------------------" -ForegroundColor DarkYellow
Write-Host ""

# --------------------------------------------------------------- 1. Python
$python = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) {
    Write-Host "  Python non risulta installato: senza non posso proseguire." -ForegroundColor Red
    Write-Host "  Scaricalo da https://www.python.org/downloads/ e rilancia."
    try { Read-Host "  Invio per chiudere" } catch { }
    exit 1
}
$python = $python.Source
$pythonw = Join-Path (Split-Path -Parent $python) "pythonw.exe"
if (-not (Test-Path $pythonw)) { $pythonw = $python }
Passo "Python trovato: $python"

Passo "Controllo le librerie necessarie..."
& $python -m pip install --quiet --disable-pip-version-check streamlit pywebview 2>&1 | Out-Null

# ------------------------------------------------- 2. chiudo se e' in esecuzione
Get-CimInstance Win32_Process -Filter "Name like '%python%'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and ($_.CommandLine -like "*avvia.py*" -or $_.CommandLine -like "*streamlit*run*app.py*") } |
    ForEach-Object {
        Passo "Chiudo l'istanza aperta (PID $($_.ProcessId))"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
Start-Sleep -Milliseconds 700

# ------------------------------------------------------------ 3. sposto i file
if ($origine -ieq $destinazione) {
    Passo "Gia' nella cartella di installazione."
} else {
    if (Test-Path $destinazione) {
        Passo "Trovata un'installazione precedente: conservo dati e impostazioni."
        $vecchiDati = Join-Path $destinazione "dati"
        $nuoviDati = Join-Path $origine "dati"
        if ((Test-Path $vecchiDati) -and -not (Test-Path $nuoviDati)) {
            Move-Item $vecchiDati $nuoviDati
        }
        Remove-Item $destinazione -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destinazione) | Out-Null
    Set-Location $env:TEMP           # non posso cancellare la cartella in cui mi trovo
    Copy-Item $origine $destinazione -Recurse -Force
    $prova = Join-Path $destinazione "app.py"
    if (-not (Test-Path $prova)) {
        Write-Host "  La copia non e' riuscita: lascio tutto dov'era." -ForegroundColor Red
        try { Read-Host "  Invio per chiudere" } catch { }
        exit 1
    }
    Passo "Copiato in $destinazione"
    try {
        Remove-Item $origine -Recurse -Force
        Passo "Rimossa la vecchia cartella $origine"
    } catch {
        Write-Host "  Non sono riuscito a togliere ${origine}: cancellala pure a mano." -ForegroundColor Yellow
    }
}

$avvio = Join-Path $destinazione "avvia.py"
$icona = Join-Path $destinazione "FantAiuto.ico"

# --------------------------------------------------------- 4. scorciatoie
$shell = New-Object -ComObject WScript.Shell
function Scorciatoia($percorso) {
    $lnk = $shell.CreateShortcut($percorso)
    $lnk.TargetPath = $pythonw
    $lnk.Arguments = '"' + $avvio + '"'
    $lnk.WorkingDirectory = $destinazione
    $lnk.IconLocation = $icona
    $lnk.Description = "Assistente per l'asta e la formazione del fantacalcio"
    $lnk.Save()
}

$menu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
Scorciatoia (Join-Path $menu "$NOME.lnk")
Passo "Aggiunto al menu Start"

$desktop = [Environment]::GetFolderPath("Desktop")
Scorciatoia (Join-Path $desktop "$NOME.lnk")
Passo "Aggiunta la scorciatoia sul Desktop"

# ------------------------------------------- 5. aggiornamento automatico
$aggiorna = Join-Path $destinazione "aggiorna.py"
schtasks /Create /TN "$attivita" /TR "`"$pythonw`" `"$aggiorna`"" /SC HOURLY /MO 1 /ST 00:05 /F /RL LIMITED | Out-Null
Passo "Aggiornamento automatico puntato alla nuova cartella (ogni ora)"

# --------------------------------------- 6. voce in "App installate"
New-Item -Path $chiave -Force | Out-Null
$disinstalla = Join-Path $destinazione "disinstalla.ps1"
$dimensione = [int]((Get-ChildItem $destinazione -Recurse -File |
                     Measure-Object Length -Sum).Sum / 1KB)
Set-ItemProperty $chiave DisplayName        $NOME
Set-ItemProperty $chiave DisplayVersion     "1.0"
Set-ItemProperty $chiave Publisher          "uso personale"
Set-ItemProperty $chiave DisplayIcon        $icona
Set-ItemProperty $chiave InstallLocation    $destinazione
Set-ItemProperty $chiave EstimatedSize      $dimensione -Type DWord
Set-ItemProperty $chiave NoModify           1 -Type DWord
Set-ItemProperty $chiave NoRepair           1 -Type DWord
Set-ItemProperty $chiave UninstallString ("powershell -ExecutionPolicy Bypass -File `"$disinstalla`"")
Passo "Registrato in App installate"

Write-Host ""
Write-Host "  Fatto." -ForegroundColor Green
Write-Host "  Trovi FantAiuto nel menu Start e sul Desktop."
Write-Host "  Installato in: $destinazione"
Write-Host "  Per toglierlo: Impostazioni > App installate > FantAiuto,"
Write-Host "                 oppure disinstalla.ps1 nella cartella."
Write-Host ""
try { Read-Host "  Invio per chiudere" } catch { }
