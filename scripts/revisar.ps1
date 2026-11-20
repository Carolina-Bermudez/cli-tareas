# scripts/revisar.ps1
# Revisa lo que vas a commitear con el subagente revisor (solo lectura), sin abrir la pantalla de OpenCode.
# Uso: git add ...  y luego  .\scripts\revisar.ps1   (sale con 0 si el revisor dice OK, con 1 si no)

# Windows: leer y escribir en UTF-8, para que las tildes del diff no lleguen como «??».
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

$diff = git diff --staged
if (-not $diff) {
    [Console]::Error.WriteLine("No hay nada preparado: haz git add primero.")
    exit 1
}

$tarea = "Revisa SOLO este diff, que te llega por la entrada estándar: no explores el repositorio ni leas otros ficheros. Aplica tus normas. Acaba con una línea: VEREDICTO: OK o VEREDICTO: CAMBIAR."
$segundos = 300   # con los modelos gratuitos, la revisión puede tardar unos 3 minutos

# El revisor se lanza aparte para poder ponerle un tiempo máximo, como el «timeout» del script de bash.
$trabajo = Start-Job -ScriptBlock {
    param($carpeta, $diff, $tarea)
    Set-Location $carpeta
    $OutputEncoding = [System.Text.UTF8Encoding]::new()
    $diff | opencode run --agent revisor $tarea
} -ArgumentList $PWD.Path, ($diff -join "`n"), $tarea

if (-not (Wait-Job $trabajo -Timeout $segundos)) {
    Stop-Job $trabajo
    Remove-Job $trabajo -Force
    [Console]::Error.WriteLine("El revisor no ha respondido en $segundos segundos.")
    exit 1
}

$revision = Receive-Job $trabajo | Out-String
Remove-Job $trabajo -Force
Write-Output $revision
if ($revision -match "(?m)^VEREDICTO: OK") { exit 0 } else { exit 1 }