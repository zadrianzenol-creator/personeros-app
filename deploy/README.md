# Self-hosting en este laptop (Sistema de Personeros)

Mismo esquema que el proyecto `checklist_chulucanas`: **SQL Server Express**
(base `personeros_chulucanas`, login dedicado `personeros_app`) + **Waitress**
(puerto 8001 local) + **NSSM** (servicio de Windows `PersonerosApp`, con
reinicio automático).

URL pública: **https://personeros.checklist.me.uk**

## Túnel compartido

El túnel público de Cloudflare (`checklist-chulucanas`) es el mismo que usa el
otro proyecto — **no hay un túnel aparte para Personeros**. Vive en:

```
C:\Users\ZURIEL\Tableros\checklist_chulucanas\deploy\cloudflared-config.yml
```

Ese archivo tiene una regla de `ingress` por cada subdominio. Si agregas un
tercer sistema, se agrega ahí otra línea (nuevo hostname → nuevo puerto local)
y se reinicia el servicio `ChecklistChulucanasTunnel`.

## Instalar / reinstalar el servicio de esta app

Doble clic en **`INSTALAR.bat`** (desde el Explorador de Windows, no desde
VS Code) → aceptar el permiso de administrador.

## Comandos útiles

```powershell
Get-Service PersonerosApp
Restart-Service PersonerosApp
```

Logs: `deploy\app.log`, `deploy\app.err.log`.

## Nota

Usuario inicial: `admin` / `admin123` (cámbiala). Igual que el otro sistema,
los datos viven en este laptop — conviene respaldar `personeros_chulucanas`
periódicamente.
