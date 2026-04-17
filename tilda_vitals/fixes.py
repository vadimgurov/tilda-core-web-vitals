def make_preload_tag(url: str) -> str:
    return f'<link rel="preload" as="image" fetchpriority="high" href="{url}">'


def make_preload_tags(mobile_url: str | None, desktop_url: str | None) -> str:
    """
    Генерирует preload-тег(и) для мобильного и/или десктопного LCP.

    - Оба одинаковых URL → один тег без media
    - Разные URL → два тега с media="(max-width: 959px)" и media="(min-width: 960px)"
    - Только один из двух → один тег с соответствующим media
    """
    if not mobile_url and not desktop_url:
        return ""
    if mobile_url and desktop_url and mobile_url == desktop_url:
        return f'<link rel="preload" as="image" fetchpriority="high" href="{mobile_url}">'
    tags = []
    if mobile_url:
        tags.append(
            f'<link rel="preload" as="image" fetchpriority="high"'
            f' media="(max-width: 959px)" href="{mobile_url}">'
        )
    if desktop_url:
        tags.append(
            f'<link rel="preload" as="image" fetchpriority="high"'
            f' media="(min-width: 960px)" href="{desktop_url}">'
        )
    return "\n".join(tags)


def _preload_key(tag: str) -> tuple[str, str]:
    """
    Извлекает семантический ключ preload-тега: (href, media).
    Используется для сравнения тегов независимо от порядка атрибутов и кавычек.
    """
    import re
    href_m = re.search(r'\bhref=["\']([^"\']+)["\']', tag)
    media_m = re.search(r'\bmedia=["\']([^"\']+)["\']', tag)
    return (href_m.group(1) if href_m else "", media_m.group(1) if media_m else "")


def preloads_already_present(preload_tags: str, head_code: str) -> bool:
    """
    Возвращает True если все preload-теги из preload_tags семантически присутствуют
    в head_code — сравнивает по href и media, игнорируя порядок атрибутов и кавычки.
    """
    expected = {_preload_key(line) for line in preload_tags.splitlines() if line.strip()}
    if not expected:
        return False
    existing = {
        _preload_key(line)
        for line in head_code.splitlines()
        if "preload" in line and "image" in line
    }
    return expected.issubset(existing)


def _is_our_preload(line: str) -> bool:
    """
    Возвращает True если строка — preload-тег, созданный этой утилитой.
    Признак: rel="preload" + as="image" + fetchpriority="high" + tildacdn.com.
    Ручные preload-теги пользователя без fetchpriority="high" не затрагиваются.
    """
    return (
        ('rel="preload"' in line or "rel='preload'" in line)
        and ('as="image"' in line or "as='image'" in line)
        and ('fetchpriority="high"' in line or "fetchpriority='high'" in line)
        and "tildacdn.com" in line
    )


def patch_head_code(current_code: str, new_preloads: str) -> str:
    """
    Убирает только те preload-теги, которые были созданы этой утилитой,
    и добавляет новые в начало. Ручные preload-теги пользователя сохраняются.
    new_preloads может содержать одну или несколько строк.
    """
    lines = [
        line for line in current_code.splitlines()
        if not _is_our_preload(line)
    ]
    rest = "\n".join(lines).strip()
    if new_preloads:
        return (new_preloads + "\n" + rest).strip() + "\n"
    return rest.strip() + "\n"
