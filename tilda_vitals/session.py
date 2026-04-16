import time
from pathlib import Path

SESSION_MAX_AGE_DAYS = 25

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36"
)


class SessionExpiredError(Exception):
    pass


def is_session_valid(session_path: Path) -> bool:
    if not session_path.exists():
        return False
    age_days = (time.time() - session_path.stat().st_mtime) / 86400
    return age_days < SESSION_MAX_AGE_DAYS


def login_wizard(session_path: Path) -> None:
    """
    Открывает headed-браузер, ждёт пока пользователь войдёт в Tilda,
    сохраняет сессию в session_path.
    """
    from playwright.sync_api import sync_playwright

    print("\n  Открываем браузер. Войдите в свой аккаунт Tilda.")
    print("  Окно закроется автоматически после входа.")
    input("  [Нажмите Enter для открытия браузера]")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(user_agent=USER_AGENT)
        page = ctx.new_page()
        page.goto("https://tilda.cc/login/", wait_until="domcontentloaded")
        print("  Ожидаем входа...")
        page.wait_for_url("**/projects/**", timeout=300_000)
        session_path.parent.mkdir(parents=True, exist_ok=True)
        ctx.storage_state(path=str(session_path))
        browser.close()

    print("  ✓ Сессия сохранена.\n")


def load_session(playwright, session_path: Path):
    """
    Загружает сохранённую сессию. Возвращает BrowserContext.
    Выбрасывает SessionExpiredError если сессия истекла.
    """
    browser = playwright.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage",
              "--disable-blink-features=AutomationControlled"],
    )
    ctx = browser.new_context(
        user_agent=USER_AGENT,
        storage_state=str(session_path),
        device_scale_factor=2,
    )
    ctx.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    probe = ctx.new_page()
    probe.goto("https://tilda.cc/projects/", wait_until="domcontentloaded", timeout=20_000)
    if "login" in probe.url:
        probe.close()
        ctx.close()
        browser.close()
        raise SessionExpiredError(
            "Сессия истекла или недействительна. Запустите: tilda-vitals login"
        )
    probe.close()
    return ctx
