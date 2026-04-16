@echo off
chcp 65001 >nul
echo.
echo === Установка tilda-vitals ===
echo.

set PYTHON=

REM Пробуем python из PATH
python --version >nul 2>&1
if %errorlevel% equ 0 set PYTHON=python

REM Пробуем py launcher
if not defined PYTHON (
    py --version >nul 2>&1
    if %errorlevel% equ 0 set PYTHON=py
)

REM Ищем в типичных папках
if not defined PYTHON (
    for %%v in (313 312 311 310) do (
        if not defined PYTHON (
            if exist "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe" (
                set PYTHON=%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe
            )
        )
    )
)
if not defined PYTHON (
    for %%v in (313 312 311 310) do (
        if not defined PYTHON (
            if exist "C:\Python%%v\python.exe" (
                set PYTHON=C:\Python%%v\python.exe
            )
        )
    )
)

if not defined PYTHON (
    echo Ошибка: Python не найден.
    echo.
    echo Скачайте Python с https://python.org/downloads
    echo При установке поставьте галочку "Add Python to PATH"
    echo.
    pause
    goto :eof
)

for /f "tokens=*" %%i in ('"%PYTHON%" --version 2^>^&1') do echo %%i - OK

echo Скачиваем установщик...
"%PYTHON%" -c "import urllib.request, os; urllib.request.urlretrieve('https://raw.githubusercontent.com/vadimgurov/tilda-core-web-vitals/main/install_helper.py', os.path.join(os.environ['TEMP'], 'tv_install.py'))"
if %errorlevel% neq 0 (
    echo Ошибка при скачивании. Проверьте подключение к интернету.
    pause
    goto :eof
)

"%PYTHON%" "%TEMP%\tv_install.py"
pause
\r