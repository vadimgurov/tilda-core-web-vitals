@echo off
echo.
echo === Установка tilda-vitals ===
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Ошибка: Python не найден.
    echo Скачайте Python с https://python.org/downloads
    echo При установке поставьте галочку "Add Python to PATH"
    pause
    exit /b 1
)

echo Скачиваем установщик...
python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/vadimgurov/tilda-core-web-vitals/main/install_helper.py', '%TEMP%\\tv_install.py')"
if %errorlevel% neq 0 (
    echo Ошибка при скачивании. Проверьте подключение к интернету.
    pause
    exit /b 1
)

python "%TEMP%\tv_install.py"
pause
