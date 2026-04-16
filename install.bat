@echo off
echo.
echo === tilda-vitals installer ===
echo.

set PYTHON=

python --version 1>nul 2>nul
if %errorlevel% equ 0 set PYTHON=python

if not defined PYTHON (
    py --version 1>nul 2>nul
    if %errorlevel% equ 0 set PYTHON=py
)

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
    echo ERROR: Python not found.
    echo.
    echo Download from https://python.org/downloads
    echo During install check "Add Python to PATH"
    echo.
    pause
    goto :eof
)

for /f "tokens=*" %%i in ('"%PYTHON%" --version 2^>^&1') do echo %%i - OK

echo Downloading installer...
"%PYTHON%" -c "import urllib.request, ssl, os; ctx = ssl._create_unverified_context(); req = urllib.request.urlopen('https://raw.githubusercontent.com/vadimgurov/tilda-core-web-vitals/main/install_helper.py', context=ctx); open(os.path.join(os.environ['TEMP'], 'tv_install.py'), 'wb').write(req.read())"
if %errorlevel% neq 0 (
    echo Download failed. Check internet connection.
    pause
    goto :eof
)

"%PYTHON%" "%TEMP%\tv_install.py"
pause
