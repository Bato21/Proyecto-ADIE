param(
    [switch]$SkipNotebooks,
    [switch]$SkipDjango,
    [switch]$SkipArtifacts,
    [int]$NotebookTimeout = 1800
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Invoke-CommandOrFail {
    param([string]$Command)

    Write-Host "   $Command" -ForegroundColor DarkGray
    Invoke-Expression $Command

    if ($LASTEXITCODE -ne 0) {
        throw "Falló comando: $Command"
    }
}

Write-Step "Validación estructural básica"
$requiredPaths = @(
    "README.md",
    "docs/README.md",
    "docs/INICIO.txt",
    "notebooks/00_pipeline_maestra_grd_2024.ipynb",
    "notebooks/01_carga_limpieza_base_grd_2024.ipynb",
    "notebooks/02_analisis_regional_severidad_grd_2024.ipynb",
    "notebooks/03_analisis_comunal_hospitalario_grd_2024.ipynb",
    "notebooks/04_exportacion_traslados_django_grd_2024.ipynb",
    "scripts/grd_common.py",
    "scripts/validate_outputs.py"
)

foreach ($relativePath in $requiredPaths) {
    if (-not (Test-Path $relativePath)) {
        throw "Falta ruta obligatoria: $relativePath"
    }
}
Write-Host "   OK: estructura mínima encontrada" -ForegroundColor Green

if (-not $SkipNotebooks) {
    Write-Step "Ejecución secuencial de notebooks"

    $notebooks = @(
        "notebooks/01_carga_limpieza_base_grd_2024.ipynb",
        "notebooks/02_analisis_regional_severidad_grd_2024.ipynb",
        "notebooks/03_analisis_comunal_hospitalario_grd_2024.ipynb",
        "notebooks/04_exportacion_traslados_django_grd_2024.ipynb"
    )

    foreach ($notebook in $notebooks) {
        Invoke-CommandOrFail "jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=$NotebookTimeout --ExecutePreprocessor.kernel_name=python3 `"$notebook`""
    }

    Write-Host "   OK: notebooks ejecutados sin error" -ForegroundColor Green
}
else {
    Write-Host "   Saltado: ejecución de notebooks" -ForegroundColor Yellow
}

if (-not $SkipArtifacts) {
    Write-Step "Validación de artefactos procesados"
    Invoke-CommandOrFail "python scripts/validate_outputs.py --processed-dir data/processed"
}
else {
    Write-Host "   Saltado: validación de artefactos" -ForegroundColor Yellow
}

if (-not $SkipDjango) {
    Write-Step "Ejecución de tests Django"
    Push-Location "app"
    try {
        Invoke-CommandOrFail "python manage.py test"
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Host "   Saltado: tests Django" -ForegroundColor Yellow
}

Write-Step "Validación completada"
Write-Host "Todo OK" -ForegroundColor Green
