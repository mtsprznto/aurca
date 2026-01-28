# --- Configuración Modular ---
# Añade aquí cualquier carpeta que quieras ignorar en tu proyecto de Binance
$CarpetasAIgnorar = @("node_modules", ".git", ".venv", "__pycache__", "dist", "build", ".idea", ".vscode")

function Show-Tree {
    param (
        [string]$Path = ".",
        [string]$Indent = ""
    )

    # Obtenemos los ítems filtrando los ignorados
    $Items = Get-ChildItem -Path $Path | Where-Object { $CarpetasAIgnorar -notcontains $_.Name }
    
    foreach ($Item in $Items) {
        $EsUltimo = $Item -eq $Items[-1]
        $Prefijo = if ($EsUltimo) { "└── " } else { "├── " }
        
        # --- Lógica de color compatible con versiones antiguas ---
        $Color = "White"
        if ($Item.PSIsContainer) { $Color = "Cyan" }

        # Imprimimos la línea
        Write-Host "$Indent$Prefijo" -NoNewline
        Write-Host "$($Item.Name)" -ForegroundColor $Color

        # Si es carpeta, recursión
        if ($Item.PSIsContainer) {
            $NuevoIndent = if ($EsUltimo) { "$Indent    " } else { "$Indent│   " }
            Show-Tree -Path $Item.FullName -Indent $NuevoIndent
        }
    }
}

Clear-Host
Write-Host "Estructura de: $(Get-Location)" -ForegroundColor Yellow
Write-Host "---------------------------------------------------"
Show-Tree
Write-Host "---------------------------------------------------"