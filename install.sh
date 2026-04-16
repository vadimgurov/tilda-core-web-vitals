#!/usr/bin/env bash
set -e

# tilda-vitals — установка и первый запуск
# Использование: curl -fsSL https://raw.githubusercontent.com/vadimgurov/tilda-core-web-vitals/main/install.sh | bash

PACKAGE_URL="https://github.com/vadimgurov/tilda-core-web-vitals/archive/refs/heads/main.zip"

echo ""
echo "=== Установка tilda-vitals ==="
echo ""

# Проверяем Python
if ! command -v python3 &>/dev/null; then
    echo "Python 3 не найден. Установите Python 3.10+ и запустите скрипт снова."
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  macOS:         brew install python3"
    exit 1
fi

PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PY_MINOR" -lt 10 ]; then
    echo "Нужен Python 3.10+. Установленная версия: 3.${PY_MINOR}"
    exit 1
fi

echo "Python найден: $(python3 --version)"

# Устанавливаем pipx если его нет
if ! command -v pipx &>/dev/null; then
    echo ""
    echo "Устанавливаем pipx..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y pipx
    elif command -v brew &>/dev/null; then
        brew install pipx
    else
        pip3 install --user pipx
    fi
    # Добавляем ~/.local/bin в PATH для текущей сессии
    export PATH="$PATH:$HOME/.local/bin"
    pipx ensurepath --quiet || true
fi

echo ""
echo "Устанавливаем tilda-vitals..."
pipx install "$PACKAGE_URL" --force --quiet

echo ""
echo "Установка завершена. Запускаем..."
echo ""

tilda-vitals
