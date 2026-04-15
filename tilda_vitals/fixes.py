def build_optim_url(static_url: str) -> str:
    """
    Преобразует URL изображения Tilda CDN для оптимизации:
      static.tildacdn.com/stor.../file.jpg
        → optim.tildacdn.com/stor.../-/resize/400x400/-/format/webp/file.jpg.webp

    Для внешних URL (не static.tildacdn.com) возвращает как есть.
    """
    if "static.tildacdn.com" not in static_url:
        return static_url
    url = static_url.replace("static.tildacdn.com", "optim.tildacdn.com")
    idx = url.rfind("/")
    return url[:idx] + "/-/resize/400x400/-/format/webp/" + url[idx + 1:] + ".webp"


def make_preload_tag(optim_url: str) -> str:
    return f'<link rel="preload" as="image" fetchpriority="high" href="{optim_url}">'


def patch_head_code(current_code: str, new_preload: str) -> str:
    """
    Убирает существующий preload для optim.tildacdn.com и добавляет новый в начало.
    Все остальные теги HEAD сохраняются без изменений.
    """
    lines = [
        line for line in current_code.splitlines()
        if not (
            ('rel="preload"' in line or "rel='preload'" in line)
            and "optim.tildacdn.com" in line
        )
    ]
    rest = "\n".join(lines).strip()
    return (new_preload + "\n" + rest).strip() + "\n"
