#!/usr/bin/env bash
set -e

GITHUB_ZIP="https://github.com/vadimgurov/tilda-core-web-vitals/archive/refs/heads/main.zip"
INSTALL_DIR="$HOME/.tilda-vitals"
BIN_DIR="$HOME/.local/bin"

echo ""
echo "=== Установка tilda-vitals ==="
echo ""

# Проверяем Python
if ! command -v python3 &>/dev/null; then
    echo "Ошибка: Python 3 не найден."
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  macOS:         brew install python3"
    exit 1
fi

PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PY_MINOR" -lt 10 ]; then
    echo "Ошибка: нужен Python 3.10+. Установлен: 3.${PY_MINOR}"
    exit 1
fi

echo "Python $(python3 --version) — OK"

# Скачиваем архив
echo "Скачиваем скрипты..."
TMP_ZIP=$(mktemp /tmp/tilda-vitals-XXXX.zip)
if command -v curl &>/dev/null; then
    curl -fsSL "$GITHUB_ZIP" -o "$TMP_ZIP"
elif command -v wget &>/dev/null; then
    wget -qO "$TMP_ZIP" "$GITHUB_ZIP"
else
    echo "Ошибка: нужен curl или wget."
    exit 1
fi

# Распаковываем в каталог установки
echo "Распаковываем..."
rm -rf "$INSTALL_DIR/tilda_vitals"
python3 -c "
import zipfile, shutil, os
with zipfile.ZipFile('$TMP_ZIP') as z:
    z.extractall('/tmp/tilda-vitals-extract')
src = '/tmp/tilda-vitals-extract/tilda-core-web-vitals-main/tilda_vitals'
dst = '$INSTALL_DIR/tilda_vitals'
os.makedirs('$INSTALL_DIR', exist_ok=True)
if os.path.exists(dst):
    shutil.rmtree(dst)
shutil.copytree(src, dst)
shutil.rmtree('/tmp/tilda-vitals-extract')
"
rm -f "$TMP_ZIP"

# Создаём виртуальное окружение и ставим зависимости
echo "Устанавливаем зависимости..."
python3 -m venv "$INSTALL_DIR/venv" --upgrade-deps
"$INSTALL_DIR/venv/bin/pip" install --quiet playwright requests pydantic
"$INSTALL_DIR/venv/bin/playwright" install chromium

# Создаём команду tilda-vitals
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/tilda-vitals" << EOF
#!/usr/bin/env bash
PYTHONPATH="$INSTALL_DIR" exec "$INSTALL_DIR/venv/bin/python" -m tilda_vitals.cli "\$@"
EOF
chmod +x "$BIN_DIR/tilda-vitals"

# Добавляем ~/.local/bin в PATH если его там нет
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "Добавьте в конец ~/.bashrc или ~/.zshrc:"
    echo "  export PATH=\"\$PATH:$BIN_DIR\""
    echo ""
    export PATH="$PATH:$BIN_DIR"
fi

echo ""
echo "Установка завершена. Запускаем..."
echo ""

exec "$BIN_DIR/tilda-vitals" check </dev/tty
