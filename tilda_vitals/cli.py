#!/usr/bin/env python3
"""
tilda-vitals — утилита для улучшения LCP на сайтах Tilda.

Использование:
  tilda-vitals              # проверить, показать что нужно исправить
  tilda-vitals --apply      # проверить и применить без подтверждения
  tilda-vitals --page /alias  # обработать одну страницу
  tilda-vitals login        # обновить сессию (войти заново)
  tilda-vitals config       # изменить настройки
"""

import argparse
import subprocess
import sys
import time

from .config import Config, SESSION_PATH, load_config, save_config
from . import api, browser, fixes
from .session import (
    SessionExpiredError,
    SESSION_MAX_AGE_DAYS,
    is_session_valid,
    load_session,
    login_wizard,
)


# ──────────────────────────────────────────────────────────────────────────────
# Автоустановка Chromium
# ──────────────────────────────────────────────────────────────────────────────

def _ensure_chromium() -> None:
    """Устанавливает Chromium если он ещё не скачан."""
    from pathlib import Path
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            exe = p.chromium.executable_path
        if Path(exe).exists():
            return
    except Exception:
        pass

    print("Скачиваем браузер Chromium (один раз, займёт около минуты)...")
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True,
    )
    print("✓ Chromium установлен.\n")


# ──────────────────────────────────────────────────────────────────────────────
# Мастер первого запуска
# ──────────────────────────────────────────────────────────────────────────────

def run_config_wizard() -> Config:
    print("\n=== Добро пожаловать в tilda-vitals ===")
    print("Это мастер первоначальной настройки. Он запустится один раз.\n")

    # Шаг 1
    print("Шаг 1/4: URL вашего сайта на Tilda")
    print("  Пример: https://myflowers.ru")
    site_url = input("  > ").strip().rstrip("/")
    if not site_url.startswith("http"):
        site_url = "https://" + site_url

    # Шаг 2
    print("\nШаг 2/4: ID проекта Tilda")
    print("  Откройте tilda.cc/projects/ и скопируйте число из URL проекта.")
    print("  Пример: 1844654")
    project_id = input("  > ").strip()

    # Шаг 3 — с проверкой API-ключей
    print("\nШаг 3/4: API-ключи Tilda")
    print("  В личном кабинете Tilda: Настройки сайта → Экспорт → API интеграции")
    while True:
        public_key = input("  Public key > ").strip()
        secret_key = input("  Secret key > ").strip()
        cfg = Config(
            site_url=site_url,
            project_id=project_id,
            tilda_public_key=public_key,
            tilda_secret_key=secret_key,
        )
        print("  Проверяем ключи...", end=" ", flush=True)
        try:
            pages = api.get_pages(cfg)
            print(f"✓ Найдено {len(pages)} страниц.")
            break
        except RuntimeError as e:
            print(f"\n  Ошибка: {e}")
            print("  Попробуйте ввести ключи ещё раз.\n")

    save_config(cfg)
    print("  ✓ Настройки сохранены.\n")

    # Шаг 4
    print("Шаг 4/4: Вход в редактор Tilda")
    _ensure_chromium()
    login_wizard(SESSION_PATH)

    return cfg


# ──────────────────────────────────────────────────────────────────────────────
# Основной цикл обработки LCP
# ──────────────────────────────────────────────────────────────────────────────

def run_fix(cfg: Config, args) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        try:
            ctx = load_session(p, SESSION_PATH)
        except SessionExpiredError as e:
            print(f"\nОшибка: {e}")
            sys.exit(1)

        try:
            _do_fix(cfg, args, ctx)
        except KeyboardInterrupt:
            print("\nПрервано.")
        finally:
            ctx.close()


def _do_fix(cfg: Config, args, ctx) -> None:
    page = ctx.new_page()

    # ── Получаем список страниц ──
    print("Получаем список страниц из Tilda API...", end=" ", flush=True)
    try:
        all_pages = api.get_pages(cfg)
    except RuntimeError as e:
        print(f"\nОшибка: {e}")
        sys.exit(1)

    store_pages = [pg for pg in all_pages if pg.get("alias", "").strip("/")]
    print(f"({len(store_pages)} страниц)\n")

    # ── Фильтр по --page ──
    if args.page:
        target = args.page.strip("/")
        store_pages = [pg for pg in store_pages if pg.get("alias", "").strip("/") == target]
        if not store_pages:
            valid = [f'/{pg.get("alias","").strip("/")}' for pg in all_pages if pg.get("alias","").strip("/")]
            print(f"Страница {args.page!r} не найдена.")
            print("Доступные страницы:")
            for v in valid:
                print(f"  {v}")
            sys.exit(1)

    # ── Фаза проверки (dry-run для всех) ──
    print("Проверяем страницы:")
    needs_update: list[dict] = []
    no_image_count = already_ok_count = 0

    for page_info in store_pages:
        alias = "/" + page_info.get("alias", "").strip("/")
        print(f"  {alias:<30}", end=" ", flush=True)

        try:
            static_url = browser.find_lcp_image(page, cfg.site_url, alias)
        except Exception as e:
            print(f"ОШИБКА: {e}")
            continue

        if not static_url:
            print("— нет изображений товаров, пропуск")
            no_image_count += 1
            time.sleep(0.5)
            continue

        optim_url = fixes.build_optim_url(static_url)

        # Проверяем текущий HEAD-код
        try:
            browser.open_head_editor(page, cfg.project_id, str(page_info["id"]))
            current_code = browser.read_head_code(page)
        except Exception as e:
            print(f"ОШИБКА (редактор): {e}")
            continue

        if optim_url in current_code:
            print("✓ уже настроено")
            already_ok_count += 1
        else:
            print("⚠ нужно обновить preload")
            needs_update.append({
                "page_info": page_info,
                "alias": alias,
                "static_url": static_url,
                "optim_url": optim_url,
                "current_code": current_code,
            })

        time.sleep(0.5)

    # ── Итог проверки ──
    print()
    if not needs_update:
        print(f"Всё в порядке: все страницы уже настроены ({already_ok_count} ✓, {no_image_count} без товаров).")
        page.close()
        return

    print(f"Проверка завершена: {already_ok_count} уже настроено, {no_image_count} без товаров, {len(needs_update)} требуют обновления.")

    # ── Подтверждение ──
    if not args.apply:
        answer = input("\nПрименить изменения? [y/N]: ").strip().lower()
        if answer not in ("y", "д", "да", "yes"):
            print("Отменено.")
            page.close()
            return

    # ── Применяем обновления ──
    print(f"\n{'─' * 50}")
    print(f"Обновляем {len(needs_update)} страниц...")
    print(f"{'─' * 50}\n")
    updated = errors = 0

    for i, item in enumerate(needs_update, 1):
        page_info = item["page_info"]
        alias = item["alias"]
        page_id = str(page_info["id"])

        print(f"  [{i}/{len(needs_update)}] {alias}")
        print(f"    → Нашли главное изображение:")
        print(f"        {item['static_url']}")

        optim_url = item["optim_url"]
        print(f"    → Преобразуем URL для оптимизации:")
        print(f"        {optim_url}")

        preload_tag = fixes.make_preload_tag(optim_url)
        print(f"    → Вставляем в HEAD страницы:")
        print(f"        {preload_tag}")

        try:
            # Открываем редактор заново (страница могла устареть)
            browser.open_head_editor(page, cfg.project_id, page_id)
            current_code = browser.read_head_code(page)
            new_code = fixes.patch_head_code(current_code, preload_tag)
            browser.write_head_code(page, new_code)

            if not args.no_publish:
                print(f"    → Публикуем страницу...", end=" ", flush=True)
                result = browser.publish_page(page, cfg.project_id, page_id)
                pub_ok = result and ("publishonepage" in result or "OK" in result)
                if pub_ok:
                    print("✓")
                else:
                    print(f"(ответ сервера: {result!r})")

            print(f"    ✓ Готово\n")
            updated += 1

        except Exception as e:
            print(f"    ОШИБКА: {e}\n")
            errors += 1

        time.sleep(0.8)

    page.close()

    # ── Итог ──
    print(
        f"Итого: {updated} обновлено, {already_ok_count} уже ок, "
        f"{no_image_count} без изображений, {errors} ошибок"
    )


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="tilda-vitals",
        description="Улучшение LCP для сайтов на Tilda",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Примеры:\n"
            "  tilda-vitals              # проверить, показать что нужно\n"
            "  tilda-vitals --apply      # проверить и применить\n"
            "  tilda-vitals --page /my-page  # обработать одну страницу\n"
            "  tilda-vitals login        # войти заново\n"
            "  tilda-vitals config       # изменить настройки\n"
        ),
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="fix",
        choices=["fix", "login", "config"],
        help="Команда (по умолчанию: fix)",
    )
    parser.add_argument("--page", metavar="PATH", help="Обработать только эту страницу")
    parser.add_argument("--apply", action="store_true", help="Применить без подтверждения")
    parser.add_argument("--no-publish", action="store_true", dest="no_publish",
                        help="Сохранить HEAD-код, но не публиковать")

    args = parser.parse_args()

    # ── Команда: login ──
    if args.command == "login":
        _ensure_chromium()
        login_wizard(SESSION_PATH)
        return

    # ── Команда: config ──
    if args.command == "config":
        run_config_wizard()
        return

    # ── Команда: fix (по умолчанию) ──
    cfg = load_config()
    if cfg is None:
        cfg = run_config_wizard()
    else:
        # Предупреждение о стареющей сессии
        if SESSION_PATH.exists():
            import time as _time
            age_days = (_time.time() - SESSION_PATH.stat().st_mtime) / 86400
            if age_days >= SESSION_MAX_AGE_DAYS - 3:
                print(
                    f"Предупреждение: сессия создана {int(age_days)} дней назад. "
                    "При ошибках запустите: tilda-vitals login\n"
                )

        if not is_session_valid(SESSION_PATH):
            print("Сессия отсутствует или устарела. Нужно войти в Tilda.")
            login_wizard(SESSION_PATH)

    run_fix(cfg, args)


if __name__ == "__main__":
    main()
