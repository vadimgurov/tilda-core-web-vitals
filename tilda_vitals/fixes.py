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


def patch_head_code(current_code: str, new_preloads: str) -> str:
    """
    Убирает существующие preload-теги для tildacdn.com и добавляет новые в начало.
    new_preloads может содержать одну или несколько строк.
    Все остальные теги HEAD сохраняются без изменений.
    """
    lines = [
        line for line in current_code.splitlines()
        if not (
            ('rel="preload"' in line or "rel='preload'" in line)
            and "tildacdn.com" in line
        )
    ]
    rest = "\n".join(lines).strip()
    if new_preloads:
        return (new_preloads + "\n" + rest).strip() + "\n"
    return rest.strip() + "\n"
