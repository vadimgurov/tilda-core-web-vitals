"""
Все взаимодействия с браузером:
- живой сайт (измерение LCP через PerformanceObserver)
- редактор Tilda (HEAD-код, публикация)
"""

import time

# JavaScript: подписывается на LCP-события с buffered=true и возвращает URL
# финального LCP-кандидата. Резолвится через 2 секунды после последнего изменения
# (LCP может обновляться по мере подгрузки lazy-load контента).
# Абсолютный таймаут — 10 секунд.
_LCP_JS = """
    () => new Promise(resolve => {
        let lastUrl = null;
        let debounce = null;
        const done = () => resolve(lastUrl);
        const obs = new PerformanceObserver(list => {
            for (const e of list.getEntries()) {
                if (e.url) lastUrl = e.url;
            }
            clearTimeout(debounce);
            debounce = setTimeout(done, 2000);
        });
        obs.observe({ type: 'largest-contentful-paint', buffered: true });
        setTimeout(done, 10000);
    })
"""


def find_lcp_image(page, site_url: str, alias: str) -> str | None:
    """
    Открывает страницу сайта в мобильном viewport (390×844),
    измеряет LCP через PerformanceObserver и возвращает URL LCP-изображения,
    или None если LCP-элемент не является изображением.
    """
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{site_url}{alias}", wait_until="networkidle")
    lcp_url = page.evaluate(_LCP_JS)
    return lcp_url if lcp_url else None


def check_page_preload(page, url: str) -> dict:
    """
    Открывает публичную страницу, измеряет LCP через PerformanceObserver
    и проверяет наличие preload-тега для LCP-изображения.

    Возвращает dict:
      status: "no_lcp_image" | "preload_ok" | "preload_missing" | "preload_wrong"
      lcp_url:  URL реального LCP-изображения
      optim_url:  рекомендуемый оптимизированный URL
      preload_tag: рекомендуемый тег для вставки в HEAD
      existing_preloads: список href всех preload-тегов с as="image" на странице
    """
    from .fixes import make_preload_tag

    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(url, wait_until="networkidle")

    lcp_url = page.evaluate(_LCP_JS)
    if not lcp_url:
        return {"status": "no_lcp_image"}

    preload_tag = make_preload_tag(lcp_url)

    # Собираем все preload as="image" теги на странице
    existing_preloads = page.evaluate(
        "() => Array.from("
        "  document.querySelectorAll('link[rel=\"preload\"][as=\"image\"]')"
        ").map(el => el.getAttribute('href'))"
    )

    def url_path(u: str) -> str:
        """Возвращает путь URL без схемы и хоста для нормализованного сравнения."""
        from urllib.parse import urlparse
        parsed = urlparse(u)
        return parsed.path + ("?" + parsed.query if parsed.query else "")

    lcp_path = url_path(lcp_url)
    preload_paths = [url_path(u) for u in (existing_preloads or [])]

    if lcp_path in preload_paths:
        status = "preload_ok"
    elif existing_preloads:
        status = "preload_wrong"
    else:
        status = "preload_missing"

    return {
        "status": status,
        "lcp_url": lcp_url,
        "preload_tag": preload_tag,
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
