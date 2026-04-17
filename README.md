# tilda-vitals

Утилита для ускорения сайта на Tilda и улучшения позиций в поиске Google.

---

## Как проверить скорость своего сайта

Google Search Console — бесплатный инструмент Google, который показывает как ваш сайт
выглядит в глазах поисковика. В том числе — насколько быстро загружаются страницы.

### Как попасть в Search Console

1. Откройте [search.google.com/search-console](https://search.google.com/search-console/)
2. Войдите через Google-аккаунт, которым управляете сайтом
3. Если сайт ещё не добавлен — нажмите **Добавить ресурс**, введите URL сайта и подтвердите
   права (например, через Google Analytics или HTML-тег в HEAD страницы)

### Где смотреть Core Web Vitals

В левом меню выберите **Основные веб-показатели** (раздел «Качество страниц»).

Вы увидите график с тремя группами страниц:
- **Хорошие** — LCP < 2.5 с, загружаются быстро
- **Требуют улучшения** — LCP 2.5–4 с
- **Неудовлетворительные** — LCP > 4 с, Google считает страницы медленными

Нажмите на группу — откроется список конкретных страниц с проблемами.

> Search Console показывает реальные данные от пользователей за последние 28 дней,
> а не лабораторные замеры. Данные появляются только если на сайт заходит достаточно
> людей — для новых или малопосещаемых сайтов раздел может быть пустым.

### После применения tilda-vitals

Изменения в Search Console видны через **4–6 недель** — столько времени нужно чтобы
накопились новые данные от реальных пользователей. Для быстрой проверки что preload
действительно работает — используйте команду `tilda-vitals check` (смотрите раздел ниже).

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

Скрипт добавляет в код каждой страницы один или два тега — подсказки для браузера загрузить
изображение немедленно, не дожидаясь JavaScript. Мобильные и десктопные устройства получают
разные размеры изображений, поэтому для каждого варианта свой тег:

```html
<!-- для мобильных устройств (до 959px) -->
<link rel="preload" as="image" fetchpriority="high" media="(max-width: 959px)" href="...">
<!-- для десктопа (от 960px) -->
<link rel="preload" as="image" fetchpriority="high" media="(min-width: 960px)" href="...">
```

Браузер активирует только тот тег, который соответствует текущей ширине экрана.

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

**Шаг 1.** Установите Python: скачайте с [python.org](https://www.python.org/downloads/windows/) —
при установке поставьте галочку **"Add Python to PATH"**

*(На Windows 10/11 можно также найти **Python 3.12** в Microsoft Store)*

**Шаг 2.** Скачайте архив со скриптами:
[tilda-core-web-vitals-main.zip](https://github.com/vadimgurov/tilda-core-web-vitals/archive/refs/heads/main.zip)

**Шаг 3.** Разархивируйте в любую папку (например, на Рабочий стол).
Появится папка `tilda-core-web-vitals-main`.

**Шаг 4.** Откройте командную строку в этой папке:
в Проводнике откройте папку `tilda-core-web-vitals-main`, щёлкните на адресной строке вверху,
введите `cmd` и нажмите Enter.

**Шаг 5.** Установите зависимости — в открывшемся окне выполните по очереди:

```
pip install playwright requests pydantic
playwright install chromium
```

> Chromium (~150 МБ) скачается при выполнении второй команды.

**Шаг 6.** Запустите скрипт:

```
python -m tilda_vitals.cli
```

---

## Первый запуск

После установки сразу запускается интерактивная проверка — никакой настройки не нужно.
Скрипт спрашивает URL и проверяет есть ли preload на странице:

```
Проверка страниц на наличие preload.
Введите URL страницы. Для выхода нажмите Ctrl+C.

URL > https://buy-wonder.com/catalog

Проверяем https://buy-wonder.com/catalog...

LCP-изображение (мобильный):
  https://optim.tildacdn.com/stor6463-.../-/resize/400x400/-/format/webp/e35360f2...png.webp
LCP-изображение (десктоп):
  https://optim.tildacdn.com/stor6463-.../-/cover/432x475/center/center/-/format/webp/e35360f2...png.webp

Preload тег: НЕТ ✗

Рекомендуемые теги для добавления в HEAD страницы:
  <link rel="preload" as="image" fetchpriority="high" media="(max-width: 959px)" href="https://optim.tildacdn.com/stor6463-.../-/resize/400x400/-/format/webp/e35360f2...png.webp">
  <link rel="preload" as="image" fetchpriority="high" media="(min-width: 960px)" href="https://optim.tildacdn.com/stor6463-.../-/cover/432x475/center/center/-/format/webp/e35360f2...png.webp">

Как добавить в Tilda:
  Настройки страницы → SEO → Дополнительный код HEAD → вставьте теги выше.

URL >
```

Можно проверять любые сайты на Tilda — не только свой. Выход по Ctrl+C.

---

## Автоматическое исправление своего сайта

Чтобы скрипт сам обошёл все страницы вашего сайта и автоматически проставил preload-теги,
нужна одноразовая настройка.

### Настройка (один раз)

```bash
tilda-vitals config
```

Мастер задаст 4 вопроса:

1. **URL вашего сайта** — например `https://myflowers.ru`
2. **ID проекта Tilda** — откройте [tilda.cc/projects](https://tilda.cc/projects/),
   скопируйте число из URL проекта (например `1844654`)
3. **API-ключи Tilda** — в личном кабинете: Настройки сайта → Экспорт → API интеграции,
   скопируйте Public и Secret key
4. **Вход в Tilda** — откроется браузер, войдите в аккаунт, окно закроется само

**Зачем нужны ключи и вход в браузер**

API-ключи нужны чтобы получить список страниц сайта. Вход в браузер нужен чтобы скрипт мог
открыть редактор HEAD-кода в Tilda и вставить туда preload-теги — Tilda не даёт делать это
через API, только через интерфейс редактора.

Ключи и сессия хранятся только на вашем компьютере в `~/.tilda-vitals/`. Скрипт не отправляет
никакие данные на сторонние серверы.

### Проверить и обновить все страницы

```bash
tilda-vitals
```

Обходит все страницы и обновляет их по ходу:

```
Получаем список страниц из Tilda API... (96 страниц)

Проверяем и обновляем страницы:
  [1/96] https://myflowers.ru/contacty       — LCP не изображение, пропуск
  [2/96] https://myflowers.ru/bukety         ✓ уже настроено
  [3/96] https://myflowers.ru/nedorogie-bukety ✓ уже настроено
  [4/96] https://myflowers.ru/suhocvety      → обновляем...
    → LCP мобильный:  https://optim.tildacdn.com/stor3f2a.../-/resize/400x400/-/format/webp/roses.jpg.webp
    → LCP десктоп:    https://optim.tildacdn.com/stor3f2a.../-/cover/432x475/center/center/-/format/webp/roses.jpg.webp
    → вставляем в HEAD: <link rel="preload" as="image" fetchpriority="high" media="(max-width: 959px)" href="https://optim.tildacdn.com/stor3f2a.../-/resize/400x400/-/format/webp/roses.jpg.webp">
    → вставляем в HEAD: <link rel="preload" as="image" fetchpriority="high" media="(min-width: 960px)" href="https://optim.tildacdn.com/stor3f2a.../-/cover/432x475/center/center/-/format/webp/roses.jpg.webp">
    → публикуем... ✓
    ✓ обновлено
  ...

Итого: 1 обновлено, 88 уже ок, 7 без LCP-изображения, 0 ошибок
```

### Только посмотреть что нужно исправить (без изменений)

```bash
tilda-vitals --preview
```

Показывает статус каждой страницы и спрашивает подтверждение перед применением.

### Проверить одну страницу

```bash
tilda-vitals --page /moya-stranica
```

### Войти заново (если сессия истекла)

```bash
tilda-vitals login
```

---

## Публикация страниц

**Обычный запуск (`tilda-vitals`)** — скрипт сам публикует каждую страницу сразу после изменения. Делать что-то вручную в Tilda не нужно.

**Флаг `--no-publish`** — скрипт сохранит изменения в редакторе Tilda, но не опубликует. Чтобы опубликовать вручную: откройте страницу в редакторе Tilda → кнопка «Опубликовать».

---

## Когда нужно перезапускать

Скрипт прописывает preload для того изображения, которое **первым стоит в каталоге на момент запуска**. Если ассортимент меняется — первый товар на странице тоже меняется, а значит preload начинает указывать на старую картинку и перестаёт работать.

Поэтому скрипт нужно запускать регулярно:

- После добавления новых товаров или страниц
- После перестановки товаров в каталоге
- Просто раз в месяц — на всякий случай

Скрипт сам проверяет актуальность и обновляет только те страницы, где preload устарел.

**Рекомендация:** поставьте напоминание раз в месяц и запускайте `tilda-vitals`.

---

## Как скрипт определяет LCP-изображение

Скрипт открывает каждую страницу дважды — в мобильном (390×844px, dpr=2) и десктопном
(1280×800px, dpr=1) viewport — и измеряет LCP через стандартное браузерное API —
`PerformanceObserver` с типом `largest-contentful-paint`:

```javascript
new PerformanceObserver(list => {
    const entries = list.getEntries();
    const last = entries[entries.length - 1];
    console.log(last.url); // URL реального LCP-изображения
}).observe({ type: 'largest-contentful-paint', buffered: true });
```

Это тот же механизм, который используют Google Lighthouse и PageSpeed Insights — браузер сам
определяет самый крупный элемент на экране. Скрипт берёт последнего кандидата и именно для него
строит preload-теги.

Если LCP-элемент является текстовым блоком (без изображения) — страница пропускается,
preload для текста не применяется.

---

## Обновление

**Linux / macOS** — та же команда что и при установке:

```bash
curl -fsSL https://raw.githubusercontent.com/vadimgurov/tilda-core-web-vitals/main/install.sh -o /tmp/install.sh && bash /tmp/install.sh
```

> Флаг `-o /tmp/install.sh` нужен чтобы обойти кэш и получить свежую версию.

**Windows** — скачайте свежий архив и распакуйте поверх старой папки (Шаги 2–3 из инструкции установки), затем повторно выполните команды из Шага 5.
