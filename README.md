# tilda-vitals

Утилита для ускорения сайта на Tilda и улучшения позиций в поиске Google.

---

## Зачем это нужно

**Быстрый сайт = выше в Google.**

Google с 2021 года официально учитывает скорость загрузки страниц при ранжировании.
Это называется **Core Web Vitals** — набор метрик качества страницы. Ключевая метрика —
**LCP (Largest Contentful Paint)**: время до появления главного элемента на экране
(обычно первое изображение товара).

Если два сайта одинаковы по контенту — тот, что грузится быстрее, будет выше в выдаче.

Официально об этом:
- [Core Web Vitals и Google Поиск](https://developers.google.com/search/docs/appearance/core-web-vitals)
- [Сигналы качества страницы в Google](https://developers.google.com/search/docs/appearance/page-experience)
- [Что такое Web Vitals](https://web.dev/articles/vitals)
- [Как Web Vitals влияют на бизнес](https://web.dev/case-studies/vitals-business-impact)

### Конкретно что происходит на Tilda

Tilda загружает изображения товаров через JavaScript: браузер скачивает JS,
запускает его — и только потом узнаёт о главном изображении и начинает загрузку.

| | До оптимизации | После |
|---|---|---|
| Начало загрузки изображения | ~1540 мс | ~13 мс |
| Ускорение | | **в 150 раз быстрее** |

Скрипт добавляет в код каждой страницы одну строку — подсказку для браузера загрузить
изображение немедленно, не дожидаясь JavaScript:

```html
<link rel="preload" as="image" fetchpriority="high" href="...">
```

---

## Установка на Linux

Одна команда — скачивает и запускает установщик:

```bash
curl -fsSL https://raw.githubusercontent.com/vadimgurov/tilda-core-web-vitals/main/install.sh | bash
```

Если `curl` недоступен:

```bash
wget -qO- https://raw.githubusercontent.com/vadimgurov/tilda-core-web-vitals/main/install.sh | bash
```

> Установщик проверит Python, установит пакет и сразу запустит мастер настройки.
> Python 3.10+ должен быть установлен. Если нет:
> `sudo apt install python3 python3-pip` (Ubuntu/Debian)

---

## Установка на macOS

Одна команда:

```bash
curl -fsSL https://raw.githubusercontent.com/vadimgurov/tilda-core-web-vitals/main/install.sh | bash
```

> Если Python не установлен: `brew install python3`
> Если Homebrew не установлен: [brew.sh](https://brew.sh)

---

## Установка на Windows

1. Установите Python: откройте **Microsoft Store**, найдите **Python 3.12**, нажмите «Установить»

   *(Или скачайте с [python.org](https://www.python.org/downloads/windows/) — при установке
   поставьте галочку **"Add Python to PATH"**)*

2. Откройте **PowerShell** (Win + X → Windows PowerShell) и выполните:

```powershell
pip install https://github.com/vadimgurov/tilda-core-web-vitals/archive/refs/heads/main.zip; tilda-vitals
```

> Chromium скачается автоматически при первом запуске.

---

## Первый запуск

После установки откроется мастер настройки. Он задаст 4 вопроса:

1. **URL вашего сайта** — например `https://myflowers.ru`
2. **ID проекта Tilda** — откройте [tilda.cc/projects](https://tilda.cc/projects/),
   скопируйте число из URL проекта (например `1844654`)
3. **API-ключи Tilda** — откройте [tilda.cc/en/profile/keys](https://tilda.cc/en/profile/keys/),
   создайте ключи если их нет, скопируйте Public и Secret key
4. **Вход в Tilda** — откроется браузер, войдите в аккаунт, окно закроется само

Браузер Chromium скачается автоматически на этом шаге (~150 МБ, один раз).

---

## Использование

### Проверить сайт (без изменений)

```bash
tilda-vitals
```

Показывает статус каждой страницы:
- `✓ уже настроено` — preload уже есть
- `⚠ нужно обновить preload` — нужно применить исправление
- `— нет изображений товаров, пропуск` — на странице нет блока с товарами

Затем спрашивает подтверждение перед применением.

### Применить исправления сразу

```bash
tilda-vitals --apply
```

### Проверить одну страницу

```bash
tilda-vitals --page /moya-stranica
```

### Войти заново (если сессия истекла)

```bash
tilda-vitals login
```

---

## Когда нужно перезапускать

- Добавили новые страницы с товарами
- Сменился первый товар в каталоге (изменилось главное изображение)
- Прошёл месяц с последнего запуска

**Рекомендация:** запускайте `tilda-vitals --apply` раз в месяц или после крупных обновлений каталога.

---

## Обновление

```bash
pip install --upgrade https://github.com/vadimgurov/tilda-core-web-vitals/archive/refs/heads/main.zip
```
