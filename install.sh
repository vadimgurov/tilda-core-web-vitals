#!/usr/bin/env bash
set -e

# tilda-vitals — установка и первый запуск
# Использование: curl -fsSL https://raw.githubusercontent.com/vadimgurov/tilda-vitals/main/install.sh | bash

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

PY_VERSION=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PY_VERSION" -lt 10 ]; then
    echo "Нужен Python 3.10+. Установленная версия: 3.${PY_VERSION}"
    exit 1
fi

echo "Python найден: $(python3 --version)"

# Устанавливаем пакет
echo ""
echo "Устанавливаем tilda-vitals..."
pip3 install --quiet https://github.com/vadimgurov/tilda-vitals/archive/refs/heads/main.zip

echo ""
echo "Установка завершена. Запускаем..."
echo ""

tilda-vitals
