
# BootShellReplace.ps1 - v11 - Replace shell with FL OS - dynamic
param([string]$ShellPath="$PSScriptRoot\FactoryLineGamingOS.exe")

$shellKey = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
$current = (Get-ItemProperty -Path $shellKey -Name Shell).Shell
Write-Host "Current shell: $current"

# Backup
Set-ItemProperty -Path $shellKey -Name "Shell_Backup_FL" -Value $current

# Dynamic replace - no hardcode
Set-ItemProperty -Path $shellKey -Name Shell -Value $ShellPath
Write-Host "[BootShellReplace] Shell set to $ShellPath - Reboot to apply"
