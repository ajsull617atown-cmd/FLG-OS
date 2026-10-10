
# RegistryInject.ps1 - v11 TOP - Dynamic registry injection - no hardcode paths
param([string]$AppName="FactoryLine", [string]$ExePath)

$regPath = "HKCU:\Software\FactoryLine\$AppName"
if (-not (Test-Path $regPath)) { New-Item -Path $regPath -Force | Out-Null }

# Dynamic - no hardcode values, read from env
$envVars = Get-ChildItem Env: | Where-Object { $_.Name -like "FL_*" }
foreach ($var in $envVars) {
    Set-ItemProperty -Path $regPath -Name $var.Name -Value $var.Value
}

if ($ExePath) {
    Set-ItemProperty -Path $regPath -Name "Executable" -Value $ExePath
    Write-Host "[RegistryInject] Injected $AppName -> $ExePath - Dynamic"
}
