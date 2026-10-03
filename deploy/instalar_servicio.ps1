#Requires -RunAsAdministrator
# Instala el Sistema de Personeros como servicio de Windows.
# El tunel publico (Cloudflare) es compartido con el proyecto checklist_chulucanas
# -- no hace falta instalarlo aqui, solo se agrega una regla de ingress alla.

$ProjectDir = "C:\Users\ZURIEL\Tableros\personeros"
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$ServeScript = Join-Path $ProjectDir "serve_waitress.py"
$Nssm = (Get-ChildItem -Path "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Filter "nssm.exe" -Recurse -ErrorAction SilentlyContinue |
         Where-Object { $_.FullName -like "*win64*" } | Select-Object -First 1).FullName
$hayErrores = $false

function Nssm-Run {
    param([string[]]$ArgList)
    $out = & $Nssm @ArgList 2>&1
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 3) {
        Write-Host "  [ERROR $LASTEXITCODE] nssm $($ArgList -join ' ') -> $out" -ForegroundColor Red
        $script:hayErrores = $true
    }
}

if (-not $Nssm) { Write-Host "No se encontro nssm.exe." -ForegroundColor Red; Read-Host "Enter para salir"; exit 1 }

Write-Host "== Servicio de Personeros (Waitress, puerto 8001) ==" -ForegroundColor Cyan
Nssm-Run @("stop", "PersonerosApp")
Nssm-Run @("remove", "PersonerosApp", "confirm")
Nssm-Run @("install", "PersonerosApp", $Python, $ServeScript)
Nssm-Run @("set", "PersonerosApp", "AppDirectory", $ProjectDir)
Nssm-Run @("set", "PersonerosApp", "DisplayName", "Personeros Chulucanas - App")
Nssm-Run @("set", "PersonerosApp", "Start", "SERVICE_AUTO_START")
Nssm-Run @("set", "PersonerosApp", "AppExit", "Default", "Restart")
Nssm-Run @("set", "PersonerosApp", "AppRestartDelay", "3000")
Nssm-Run @("set", "PersonerosApp", "AppStdout", (Join-Path $ProjectDir "deploy\app.log"))
Nssm-Run @("set", "PersonerosApp", "AppStderr", (Join-Path $ProjectDir "deploy\app.err.log"))
Nssm-Run @("set", "PersonerosApp", "AppRotateFiles", "1")
Nssm-Run @("set", "PersonerosApp", "AppRotateBytes", "5242880")

Write-Host "== Arrancando ==" -ForegroundColor Cyan
Nssm-Run @("start", "PersonerosApp")
Start-Sleep -Seconds 3

Write-Host ""
if ($hayErrores) {
    Write-Host "== Hubo errores (en rojo arriba). Revisa deploy\*.log ==" -ForegroundColor Red
} else {
    Write-Host "== Listo, sin errores ==" -ForegroundColor Green
}
Get-Service PersonerosApp | Format-Table -AutoSize

Write-Host ""
Read-Host "Presiona Enter para cerrar esta ventana"
