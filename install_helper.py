#!/usr/bin/env python3
"""
Установщик tilda-vitals для Windows.
Запускается автоматически из install.bat.
"""
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

GITHUB_ZIP = "https://github.com/vadimgurov/tilda-core-web-vitals/archive/refs/heads/main.zip"
INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".tilda-vitals")
BIN_DIR = os.path.join(os.path.expanduser("~"), ".local", "bin")
TMP_DIR = os.environ.get("TEMP", os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp"))


def download_and_extract():
    print("Скачиваем скрипты...")
    tmp_zip = os.path.join(TMP_DIR, "tv.zip")
    import ssl
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(GITHUB_ZIP, context=ctx) as resp:
        with open(tmp_zip, "wb") as f:
            f.write(resp.read())

    print("Распаковываем...")
    tmp_ext = os.path.join(TMP_DIR, "tv-ext")
    if os.path.exists(tmp_ext):
        shutil.rmtree(tmp_ext)
    with zipfile.ZipFile(tmp_zip) as z:
        z.extractall(tmp_ext)

    src = os.path.join(tmp_ext, "tilda-core-web-vitals-main", "tilda_vitals")
    dst = os.path.join(INSTALL_DIR, "tilda_vitals")
    os.makedirs(INSTALL_DIR, exist_ok=True)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)
    shutil.rmtree(tmp_ext)
    os.remove(tmp_zip)


def install_deps():
    print("Устанавливаем зависимости...")
    venv_dir = os.path.join(INSTALL_DIR, "venv")
    subprocess.run(
        [sys.executable, "-m", "venv", venv_dir, "--upgrade-deps"],
        check=True
    )
    pip = os.path.join(venv_dir, "Scripts", "pip.exe")
    subprocess.run([pip, "install", "--quiet", "playwright", "requests", "pydantic"], check=True)


def create_launcher():
    os.makedirs(BIN_DIR, exist_ok=True)
    launcher = os.path.join(BIN_DIR, "tilda-vitals.bat")
    py = os.path.join(INSTALL_DIR, "venv", "Scripts", "python.exe")
    with open(launcher, "w") as f:
        f.write("@echo off\n")
        f.write(f"set PYTHONPATH={INSTALL_DIR}\n")
        f.write(f'"{py}" -m tilda_vitals.cli %*\n')


def add_to_path():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS)
        try:
            path_val, _ = winreg.QueryValueEx(key, "PATH")
        except FileNotFoundError:
            path_val = ""
        if BIN_DIR not in path_val:
            new_path = (path_val + ";" + BIN_DIR).lstrip(";")
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
            print(f"\nПапка {BIN_DIR} добавлена в PATH.")
            print("Перезапустите командную строку чтобы команда 'tilda-vitals' стала доступна.")
        winreg.CloseKey(key)
    except Exception:
        pass


def main():
    try:
        download_and_extract()
        install_deps()
        create_launcher()
        add_to_path()
    except Exception as e:
        print(f"\nОшибка при установке: {e}")
        sys.exit(1)

    print("\nУстановка завершена! Запускаем...\n")

    python_exe = os.path.join(INSTALL_DIR, "venv", "Scripts", "python.exe")
    env = os.environ.copy()
    env["PYTHONPATH"] = INSTALL_DIR
    subprocess.run([python_exe, "-m", "tilda_vitals.cli", "check"], env=env)


if __name__ == "__main__":
    main()
