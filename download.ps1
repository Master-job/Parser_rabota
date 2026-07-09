param(
  [Parameter(Mandatory=$true)] [string]$Url,
  [Parameter(Mandatory=$true)] [string]$OutFile
)

if ([string]::IsNullOrWhiteSpace($Url)) { throw "Url пустой" }
if ([string]::IsNullOrWhiteSpace($OutFile)) { throw "OutFile пустой" }

$dir = Split-Path -Parent $OutFile
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }

if (Test-Path $OutFile) {
  Write-Host "Файл уже есть: $OutFile (пропускаю)"
  return
}

# Invoke-WebRequest лучше работает у тебя (пример уже открывается с 200)
Invoke-WebRequest -Uri $Url -OutFile $OutFile -TimeoutSec 120 -UseBasicParsing
Write-Host "Скачал: $OutFile"
