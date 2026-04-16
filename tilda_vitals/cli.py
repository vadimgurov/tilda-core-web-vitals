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

    if args.preview:
        _run_preview(cfg, args, page, store_pages)
    else:
        _run_apply(cfg, args, page, store_pages)

    page.close()


def _check_page(cfg, page, page_info) -> dict:
    """Проверяет страницу и возвращает dict с результатом."""
    alias = "/" + page_info.get("alias", "").strip("/")

    lcp_url = browser.find_lcp_image(page, cfg.site_url, alias)
    if not lcp_url:
        return {"status": "no_image", "alias": alias}

    preload_tag = fixes.make_preload_tag(lcp_url)
    browser.open_head_editor(page, cfg.project_id, str(page_info["id"]))
    current_code = browser.read_head_code(page)

    if lcp_url in current_code:
        return {"status": "ok", "alias": alias}

    return {
        "status": "needs_update",
        "alias": alias,
        "lcp_url": lcp_url,
        "preload_tag": preload_tag,
        "current_code": current_code,
        "page_info": page_info,
    }


def _apply_update(cfg, args, page, item) -> bool:
    """Применяет обновление к одной странице. Возвращает True при успехе."""
    page_id = str(item["page_info"]["id"])
    preload_tag = item["preload_tag"]

    print(f"    → LCP-изображение: {item['lcp_url']}")
    print(f"    → вставляем в HEAD: {preload_tag}")

    browser.open_head_editor(page, cfg.project_id, page_id)
    current_code = browser.read_head_code(page)
    new_code = fixes.patch_head_code(current_code, preload_tag)
    browser.write_head_code(page, new_code)

    if not args.no_publish:
        print(f"    → публикуем...", end=" ", flush=True)
        result = browser.publish_page(page, cfg.project_id, page_id)
        pub_ok = result and ("publishonepage" in result or "OK" in result)
        print("✓" if pub_ok else f"(ответ: {result!r})")

    print(f"    ✓ обновлено\n")
    return True


def _run_apply(cfg, args, page, store_pages) -> None:
    """Одним проходом: проверяет и сразу обновляет."""
    total = len(store_pages)
    print("Проверяем и обновляем страницы:")
    updated = already_ok = no_image = errors = 0

    for i, page_info in enumerate(store_pages, 1):
        alias = "/" + page_info.get("alias", "").strip("/")
        full_url = cfg.site_url + alias
        print(f"  [{i}/{total}] {full_url}", end=" ", flush=True)

        try:
            result = _check_page(cfg, page, page_info)
        except Exception as e:
            print(f"ОШИБКА: {e}")
            errors += 1
            continue

        if result["status"] == "no_image":
            print("— LCP не изображение, пропуск")
            no_image += 1
        elif result["status"] == "ok":
            print("✓ уже настроено")
            already_ok += 1
        else:
            print("→ обновляем...")
            try:
                _apply_update(cfg, args, page, result)
                updated += 1
            except Exception as e:
                print(f"    ОШИБКА: {e}\n")
                errors += 1

        time.sleep(0.5)

    print(
        f"\nИтого: {updated} обновлено, {already_ok} уже ок, "
        f"{no_image} без LCP-изображения, {errors} ошибок"
    )


def _run_preview(cfg, args, page, store_pages) -> None:
    """Сначала проверяет все страницы, показывает список, потом спрашивает подтверждение."""
    total = len(store_pages)
    print("Проверяем страницы:")
    needs_update: list[dict] = []
    already_ok = no_image = errors = 0

    for i, page_info in enumerate(store_pages, 1):
        alias = "/" + page_info.get("alias", "").strip("/")
        full_url = cfg.site_url + alias
        print(f"  [{i}/{total}] {full_url}", end=" ", flush=True)

        try:
            result = _check_page(cfg, page, page_info)
        except Exception as e:
            print(f"ОШИБКА: {e}")
            errors += 1
            continue

        if result["status"] == "no_image":
            print("— LCP не изображение, пропуск")
            no_image += 1
        elif result["status"] == "ok":
            print("✓ уже настроено")
            already_ok += 1
        else:
            print("⚠ нужно обновить preload")
            needs_update.append(result)

        time.sleep(0.5)

    print()
    if not needs_update:
        print(f"Всё в порядке: {already_ok} уже настроено, {no_image} без LCP-изображения.")
        return

    print(f"Проверка завершена: {already_ok} уже ок, {no_image} без LCP-изображения, {len(needs_update)} требуют обновления.")

    answer = input("\nПрименить изменения? [y/N]: ").strip().lower()
    if answer not in ("y", "д", "да", "yes"):
        print("Отменено.")
        return

    print()
    updated = 0
    for item in needs_update:
        print(f"  {item['alias']}")
        try:
            _apply_update(cfg, args, page, item)
            updated += 1
        except Exception as e:
            print(f"    ОШИБКА: {e}\n")
            errors += 1

    print(
        f"Итого: {updated} обновлено, {already_ok} уже ок, "
        f"{no_image} без товаров, {errors} ошибок"
    )


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def _print_check_result(result: dict) -> None:
    """Выводит результат проверки одной страницы."""
    status = result["status"]

    if status == "no_lcp_image":
        print("LCP-элемент не является изображением.")
        print("Preload для текстовых блоков не применяется.")
        return

    print(f"LCP-изображение:")
    print(f"  {result['lcp_url']}\n")

    if status == "preload_ok":
        print("Preload тег: ЕСТЬ ✓")
        print(f"  {result['lcp_url']}")

    elif status == "preload_wrong":
        print("Preload тег: ЕСТЬ, но указывает на другое изображение")
        print("\nТекущий preload на странице:")
        for href in result["existing_preloads"]:
            print(f"  {href}")
        print(f"\nРеальный LCP (измерено браузером):")
        print(f"  {result['lcp_url']}")
        print(f"\nРекомендуемый тег для LCP:")
        print(f"  {result['preload_tag']}")
        print("\nКак добавить в Tilda:")
        print("  Настройки страницы → SEO → Дополнительный код HEAD → вставьте тег выше.")

    else:  # preload_missing
        print("Preload тег: НЕТ ✗")
        print("\nРекомендуемый тег для добавления в HEAD страницы:")
        print(f"  {result['preload_tag']}")
        print("\nКак добавить в Tilda:")
        print("  Настройки страницы → SEO → Дополнительный код HEAD → вставьте тег выше.")


def run_check(url: str | None) -> None:
    """
    Если url задан — проверяет одну страницу.
    Если нет — запускает интерактивный цикл: спрашивает URL снова и снова до Ctrl+C.
    """
    from playwright.sync_api import sync_playwright

    _ensure_chromium()

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True,
                              args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = b.new_context()
        page = ctx.new_page()

        try:
            if url:
                print(f"\nПроверяем {url}...\n")
                result = browser.check_page_preload(page, url)
                _print_check_result(result)
            else:
                print("\nПроверка страниц на наличие preload.")
                print("Введите URL страницы. Для выхода нажмите Ctrl+C.\n")
                while True:
                    try:
                        raw = input("URL > ").strip()
                    except EOFError:
                        break
                    if not raw:
                        continue
                    if not raw.startswith(("http://", "https://")):
                        raw = "https://" + raw
                    print(f"\nПроверяем {raw}...\n")
                    try:
                        result = browser.check_page_preload(page, raw)
                        _print_check_result(result)
                    except Exception as e:
                        print(f"Ошибка: {e}")
                    print()

        except KeyboardInterrupt:
            print("\nВыход.")
        finally:
            b.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="tilda-vitals",
        description="Улучшение LCP для сайтов на Tilda",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Примеры:\n"
            "  tilda-vitals              # проверить и обновить все страницы\n"
            "  tilda-vitals --preview    # только показать что нужно исправить\n"
            "  tilda-vitals --page /my-page  # обработать одну страницу\n"
            "  tilda-vitals check https://example.com/catalog  # проверить любой сайт\n"
            "  tilda-vitals login        # войти заново\n"
            "  tilda-vitals config       # изменить настройки\n"
        ),
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="fix",
        choices=["fix", "login", "config", "check"],
        help="Команда (по умолчанию: fix)",
    )
    parser.add_argument("url", nargs="?", help="URL страницы для команды check")
    parser.add_argument("--page", metavar="PATH", help="Обработать только эту страницу")
    parser.add_argument("--preview", action="store_true", help="Только показать что нужно исправить, без применения")
    parser.add_argument("--no-publish", action="store_true", dest="no_publish",
                        help="Сохранить HEAD-код, но не публиковать")

    args = parser.parse_args()

    # ── Команда: check ──
    if args.command == "check":
        run_check(args.url)
        return

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
