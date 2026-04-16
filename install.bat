@echo off
chcp 65001 >nul

echo.
echo === Установка tilda-vitals ===
echo.

REM 1. Пробуем python/py из PATH
python --version >nul 2>&1
if %errorlevel% equ 0 ( set PYTHON=python & goto python_ok )

py --version >nul 2>&1
if %errorlevel% equ 0 ( set PYTHON=py & goto python_ok )

REM 2. Ищем через реестр (HKCU — установка для текущего пользователя)
for /f "tokens=2*" %%a in ('reg query "HKCU\Software\Python\PythonCore" /s /v ExecutablePath 2^>nul ^| findstr /i "ExecutablePath"') do set PYTHON=%%b
if defined PYTHON goto python_ok

REM 3. Ищем через реестр (HKLM — установка для всех пользователей)
for /f "tokens=2*" %%a in ('reg query "HKLM\Software\Python\PythonCore" /s /v ExecutablePath 2^>nul ^| findstr /i "ExecutablePath"') do set PYTHON=%%b
if defined PYTHON goto python_ok

REM 4. Ищем в типичных папках установки
for %%v in (313 312 311 310) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe" (
        set PYTHON=%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe
        goto python_ok
    )
    if exist "C:\Python%%v\python.exe" (
        set PYTHON=C:\Python%%v\python.exe
        goto python_ok
    )
)

echo Ошибка: Python не найден.
echo.
echo Скачайте Python с https://python.org/downloads
echo При установке поставьте галочку "Add Python to PATH"
echo.
pause
exit /b 1

:python_ok
for /f "tokens=*" %%i in ('"%PYTHON%" --version') do echo %%i - OK

echo Скачиваем установщик...
"%PYTHON%" -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/vadimgurov/tilda-core-web-vitals/main/install_helper.py', '%TEMP%\\tv_install.py')"
if %errorlevel% neq 0 (
    echo Ошибка при скачивании. Проверьте подключение к интернету.
    pause
    exit /b 1
)

"%PYTHON%" "%TEMP%\tv_install.py"
pause
