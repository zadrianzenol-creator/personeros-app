@echo off
:: Doble clic EN EL EXPLORADOR DE WINDOWS (no en VS Code) en este archivo.
:: Windows pedira permiso de administrador (clic en "Si") y luego instala solo.

powershell -NoProfile -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%~dp0instalar_servicio.ps1\"' -Verb RunAs -Wait"

echo.
echo Si no viste errores arriba, ya quedo instalado.
pause
