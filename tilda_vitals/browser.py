"""
Все взаимодействия с браузером:
- живой сайт (измерение LCP через PerformanceObserver)
- редактор Tilda (HEAD-код, публикация)
"""

import time

# init-скрипт: запускается в каждом новом документе ДО любых других скриптов.
# Собирает LCP-записи в window.__lcpUrl по мере загрузки страницы.
_LCP_INIT_SCRIPT = """
    window.__lcpUrl = null;
    new PerformanceObserver(list => {
        for (const e of list.getEntries()) {
            if (e.url) window.__lcpUrl = e.url;
        }
    }).observe({ type: 'largest-contentful-paint', buffered: true });
"""


def setup_lcp_tracking(page) -> None:
    """Регистрирует сборщик LCP. Вызывать один раз после создания страницы."""
    page.add_init_script(_LCP_INIT_SCRIPT)


def find_lcp_image(page, site_url: str, alias: str,
                   width: int = 390, height: int = 844) -> str | None:
    """
    Открывает страницу сайта в заданном viewport,
    измеряет LCP через PerformanceObserver и возвращает URL LCP-изображения,
    или None если LCP-элемент не является изображением.

    По умолчанию — мобильный viewport (390×844).
    """
    page.set_viewport_size({"width": width, "height": height})
    page.goto(f"{site_url}{alias}", wait_until="networkidle")
    # Небольшая пауза — дать браузеру зафиксировать финальный LCP после networkidle
    page.wait_for_timeout(1000)
    lcp_url = page.evaluate("() => window.__lcpUrl")
    return lcp_url if lcp_url else None


def check_page_preload(page_mobile, url: str, page_desktop=None) -> dict:
    """
    Открывает публичную страницу, измеряет LCP через PerformanceObserver
    и проверяет наличие preload-тегов для LCP-изображений.

    page_mobile — страница с device_scale_factor=2, viewport 390×844.
    page_desktop — опционально, страница с device_scale_factor=1, viewport 1280×800.

    Возвращает dict:
      status: "no_lcp_image" | "preload_ok" | "preload_missing" | "preload_wrong"
      mobile_url:  URL LCP-изображения на мобильном
      desktop_url: URL LCP-изображения на десктопе (или None)
      preload_tags: рекомендуемые теги для вставки в HEAD
      existing_preloads: список href всех preload-тегов с as="image" на странице
    """
    import re
    from .fixes import make_preload_tags

    page_mobile.set_viewport_size({"width": 390, "height": 844})
    page_mobile.goto(url, wait_until="networkidle")
    page_mobile.wait_for_timeout(1000)
    mobile_url = page_mobile.evaluate("() => window.__lcpUrl") or None

    desktop_url = None
    if page_desktop is not None:
        page_desktop.set_viewport_size({"width": 1280, "height": 800})
        page_desktop.goto(url, wait_until="networkidle")
        page_desktop.wait_for_timeout(1000)
        desktop_url = page_desktop.evaluate("() => window.__lcpUrl") or None

    if not mobile_url and not desktop_url:
        return {"status": "no_lcp_image"}

    preload_tags = make_preload_tags(mobile_url, desktop_url)

    # Собираем все preload as="image" теги на странице (проверяем по мобильной версии)
    existing_preloads = page_mobile.evaluate(
        "() => Array.from("
        "  document.querySelectorAll('link[rel=\"preload\"][as=\"image\"]')"
        ").map(el => el.getAttribute('href'))"
    )

    def url_path(u: str) -> str:
        """Возвращает путь URL без схемы и хоста для нормализованного сравнения."""
        from urllib.parse import urlparse
        parsed = urlparse(u)
        return parsed.path + ("?" + parsed.query if parsed.query else "")

    # Ожидаемые href из сгенерированных preload-тегов
    expected_hrefs = re.findall(r'href="([^"]+)"', preload_tags)
    expected_paths = [url_path(h) for h in expected_hrefs]
    existing_paths = [url_path(u) for u in (existing_preloads or [])]

    if expected_paths and all(p in existing_paths for p in expected_paths):
        status = "preload_ok"
    elif existing_preloads:
        status = "preload_wrong"
    else:
        status = "preload_missing"

    return {
        "status": status,
        "mobile_url": mobile_url,
        "desktop_url": desktop_url,
        "lcp_url": mobile_url or desktop_url,  # для обратной совместимости
        "preload_tags": preload_tags,
        "preload_tag": preload_tags,  # для обратной совместимости
        "existing_preloads": existing_preloads or [],
    }


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
