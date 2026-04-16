def make_preload_tag(url: str) -> str:
    return f'<link rel="preload" as="image" fetchpriority="high" href="{url}">'


def patch_head_code(current_code: str, new_preload: str) -> str:
    """
    Убирает существующий preload для tildacdn.com и добавляет новый в начало.
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
    return (new_preload + "\n" + rest).strip() + "\n"
