# Registra in Windows un aggiornamento automatico di FantAiuto, ogni ora.
#
# Uso:  tasto destro sul file  ->  "Esegui con PowerShell"
#       oppure da PowerShell:  .\installa_aggiornamento.ps1
#       ogni due ore:          .\installa_aggiornamento.ps1 -OgniOre 2
#
# Per disinstallarlo:          .\installa_aggiornamento.ps1 -Rimuovi

param(
    [switch]$Rimuovi,
    [int]$OgniOre = 1
)

$ErrorActionPreference = "Stop"
$nome = "FantAiuto - aggiornamento dati"
$cartella = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Rimuovi) {
    schtasks /Delete /TN "$nome" /F
    Write-Host "Aggiornamento automatico rimosso." -ForegroundColor Yellow
    exit
}

# pythonw.exe esegue senza aprire la finestra nera del terminale
$python = (Get-Command python).Source
$pythonw = Join-Path (Split-Path -Parent $python) "pythonw.exe"
if (-not (Test-Path $pythonw)) { $pythonw = $python }

$script = Join-Path $cartella "aggiorna.py"
$comando = "`"$pythonw`" `"$script`""

# HOURLY con /MO = ogni N ore, a partire dai 5 minuti dopo l'ora piena: le
# probabili formazioni e l'infermeria cambiano durante il giorno, e all'asta
# o prima della giornata un dato vecchio di un giorno e' un dato sbagliato
schtasks /Create /TN "$nome" /TR $comando /SC HOURLY /MO $OgniOre /ST 00:05 /F /RL LIMITED

Write-Host ""
Write-Host "Fatto." -ForegroundColor Green
if ($OgniOre -eq 1) { $quando = "Ogni ora" } else { $quando = "Ogni $OgniOre ore" }
Write-Host "$quando Windows riscarica i dati e ricalcola tutto (ci mette circa un minuto)."
Write-Host "Il PC deve essere acceso: se e' spento salta quel giro e riprende al successivo,"
Write-Host "oppure puoi lanciarlo a mano dal pulsante dentro l'app."
Write-Host ""
Write-Host "Log degli aggiornamenti: dati\aggiornamento.log"
Write-Host "Per toglierlo:           .\installa_aggiornamento.ps1 -Rimuovi"
