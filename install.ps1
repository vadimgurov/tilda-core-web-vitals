# tilda-vitals — установка для Windows
# Запуск: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned; .\install.ps1

$ErrorActionPreference = "Stop"

$GithubZip = "https://github.com/vadimgurov/tilda-core-web-vitals/archive/refs/heads/main.zip"
$InstallDir = "$env:USERPROFILE\.tilda-vitals"
$BinDir = "$env:USERPROFILE\.local\bin"

Write-Host ""
Write-Host "=== Установка tilda-vitals ===" -ForegroundColor Cyan
Write-Host ""

# Проверяем Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "Python $pyVersion — OK"
} catch {
    Write-Host "Ошибка: Python не найден." -ForegroundColor Red
    Write-Host "Установите Python из Microsoft Store (найдите 'Python 3.12')"
    Write-Host "или скачайте с https://python.org/downloads"
    exit 1
}

# Скачиваем архив
Write-Host "Скачиваем скрипты..."
$TmpZip = "$env:TEMP\tilda-vitals.zip"
Invoke-WebRequest -Uri $GithubZip -OutFile $TmpZip -UseBasicParsing

# Распаковываем
Write-Host "Распаковываем..."
$TmpExtract = "$env:TEMP\tilda-vitals-extract"
if (Test-Path $TmpExtract) { Remove-Item $TmpExtract -Recurse -Force }
Expand-Archive -Path $TmpZip -DestinationPath $TmpExtract -Force
Remove-Item $TmpZip

$Src = "$TmpExtract\tilda-core-web-vitals-main\tilda_vitals"
$Dst = "$InstallDir\tilda_vitals"
if (-not (Test-Path $InstallDir)) { New-Item -ItemType Directory -Path $InstallDir | Out-Null }
if (Test-Path $Dst) { Remove-Item $Dst -Recurse -Force }
Copy-Item $Src $Dst -Recurse
Remove-Item $TmpExtract -Recurse -Force

# Создаём виртуальное окружение и ставим зависимости
Write-Host "Устанавливаем зависимости..."
python -m venv "$InstallDir\venv" --upgrade-deps | Out-Null
& "$InstallDir\venv\Scripts\pip" install --quiet playwright requests pydantic

# Создаём запускающий скрипт
if (-not (Test-Path $BinDir)) { New-Item -ItemType Directory -Path $BinDir | Out-Null }
$Launcher = "$BinDir\tilda-vitals.bat"
@"
@echo off
set PYTHONPATH=$InstallDir
"$InstallDir\venv\Scripts\python" -m tilda_vitals.cli %*
"@ | Set-Content $Launcher

# Добавляем BinDir в PATH пользователя если ещё не там
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$UserPath;$BinDir", "User")
    $env:PATH += ";$BinDir"
    Write-Host ""
    Write-Host "Папка $BinDir добавлена в PATH." -ForegroundColor Yellow
    Write-Host "Перезапустите PowerShell чтобы команда 'tilda-vitals' стала доступна."
}

Write-Host ""
Write-Host "Установка завершена. Запускаем..." -ForegroundColor Green
Write-Host ""

& "$InstallDir\venv\Scripts\python" -m tilda_vitals.cli
