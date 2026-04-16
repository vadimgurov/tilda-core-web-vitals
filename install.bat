@echo off
chcp 65001 >nul

echo.
echo === Установка tilda-vitals ===
echo.

REM Пробуем python, потом py (альтернативный launcher)
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
    goto python_ok
)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=py
    goto python_ok
)

echo Ошибка: Python не найден.
echo.
echo Скачайте Python с https://python.org/downloads
echo При установке поставьте галочку "Add Python to PATH"
echo.
echo Если Python уже установлен - закройте это окно и откройте заново.
echo.
pause
exit /b 1

:python_ok
for /f "tokens=*" %%i in ('%PYTHON% --version') do echo %%i - OK

echo Скачиваем установщик...
%PYTHON% -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/vadimgurov/tilda-core-web-vitals/main/install_helper.py', '%TEMP%\\tv_install.py')"
if %errorlevel% neq 0 (
    echo Ошибка при скачивании. Проверьте подключение к интернету.
    pause
    exit /b 1
)

%PYTHON% "%TEMP%\tv_install.py"
pause
