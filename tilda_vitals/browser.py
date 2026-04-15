"""
Все взаимодействия с браузером:
- живой сайт (поиск LCP-изображения)
- редактор Tilda (HEAD-код, публикация)
"""

import time


def find_lcp_image(page, site_url: str, alias: str) -> str | None:
    """
    Открывает страницу сайта в мобильном viewport (390×844),
    ждёт загрузки карточек товаров и возвращает data-original
    первого изображения товара, или None если товаров нет.
    """
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{site_url}{alias}", wait_until="domcontentloaded")
    try:
        page.wait_for_selector(
            ".t-store__card__bgimg[data-original]", timeout=10_000
        )
    except Exception:
        return None
    return page.evaluate(
        "() => {"
        "  const el = document.querySelector('.t-store__card__bgimg[data-original]');"
        "  return el ? el.getAttribute('data-original') : null;"
        "}"
    )


def open_head_editor(page, project_id: str, page_id: str) -> None:
    """Открывает редактор HEAD-кода страницы и ждёт инициализации ACE editor."""
    page.set_viewport_size({"width": 1280, "height": 800})
    url = (
        f"https://tilda.cc/projects/editheadcode/"
        f"?projectid={project_id}&pageid={page_id}"
    )
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.aceeditor", timeout=15_000)


def read_head_code(page) -> str:
    return page.evaluate("() => window.aceeditor.getValue()")


def write_head_code(page, new_code: str) -> None:
    """Записывает новый HEAD-код и сохраняет через официальную функцию Tilda."""
    page.evaluate("(code) => { window.aceeditor.setValue(code, -1); }", new_code)
    page.evaluate("() => td__pageheadcode__saveCode()")
    try:
        page.wait_for_function(
            "() => !!document.querySelector('.td-bubble-notice')",
            timeout=12_000,
        )
    except Exception:
        # Сохранение могло пройти без видимого уведомления — не критично
        time.sleep(2)


def publish_page(page, project_id: str, page_id: str) -> str:
    """Публикует страницу через AJAX-эндпоинт Tilda."""
    return page.evaluate(
        """
        async (args) => {
            const csrf = (typeof getCSRF === 'function') ? getCSRF()
                : (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
            const fd = new FormData();
            fd.append('comm', 'pagepublish');
            fd.append('projectid', args.projectid);
            fd.append('pageid', args.pageid);
            fd.append('csrf', csrf);
            fd.append('returnjson', 'yes');
            const resp = await fetch('/page/publish/', {method: 'POST', body: fd});
            return await resp.text();
        }
        """,
        {"projectid": project_id, "pageid": str(page_id)},
    )
