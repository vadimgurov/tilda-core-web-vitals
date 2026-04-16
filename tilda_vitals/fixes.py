def build_optim_url(url: str) -> str:
    """
    Строит канонический preload URL для изображения Tilda CDN (400x400, webp).

    Принимает любой вариант URL:
      - static.tildacdn.com/stor.../file.jpg
      - optim.tildacdn.com/stor.../-/resize/240x240/-/format/webp/file.jpg.webp
    Оба дают одинаковый результат:
      → optim.tildacdn.com/stor.../-/resize/400x400/-/format/webp/file.jpg.webp

    Для URL не с tildacdn.com возвращает как есть.
    """
    if "tildacdn.com" not in url:
        return url

    # Убираем протокол и хост, получаем путь начиная со stor...
    for host in ("static.tildacdn.com/", "optim.tildacdn.com/"):
        if host in url:
            path = url.split(host, 1)[1]
            break
    else:
        return url

    # path вида: stor{id}/...возможные трансформации.../filename.ext[.webp]
    # Разбиваем на stor-id и имя файла (последний сегмент)
    parts = path.split("/")
    stor_id = parts[0]
    filename = parts[-1]

    # Убираем .webp суффикс если он есть (optim добавляет его к имени)
    if filename.endswith(".webp"):
        filename = filename[:-5]

    return (
        f"https://optim.tildacdn.com/{stor_id}"
        f"/-/resize/400x400/-/format/webp/{filename}.webp"
    )


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
