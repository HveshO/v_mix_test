# Flaky Gate — тестовое API для анализа нестабильных тестов

Небольшой сервис на **FastAPI + SQLAlchemy + Alembic + PostgreSQL**, который хранит:
- тестовые прогоны (`test_run`)
- результаты тестов в прогонах (`test_result`)
- метаданные тестов (`test_case`)

И отдаёт агрегированную статистику по “flaky” тестам.

---

## Что ожидается от кандидата

1) Исправить проблемы запуска через Docker.
2) Исправить ошибки в функционале.
3) Оптимизировать расчёт flaky.
4) Привести работу с БД к единообразию.
5) Прогнать тесты и добиться, чтобы все тесты проходили.
   - В проекте намеренно есть тест(ы) с ошибками — их нужно исправить.
6) Исправить ошибки безопасности кода.
7) Предложить архитектурные улучшения в отдельном файле `ARCHITECTURE.md`.
8) Описать что было выполнено в рамках отведённого срока по данному проекту.
9) (Будет плюсом) Развернуть базу данных на порту отличном от внутренного (5432).

---

## Содержание

- [Требования](#требования)
- [Конфигурация](#конфигурация)
- [Быстрый старт в Docker](#быстрый-старт-в-docker)
- [Локальный запуск без Docker](#локальный-запуск-без-docker)
- [Миграции](#миграции)
- [Тесты](#тесты)
- [API: ручная проверка curl](#api-ручная-проверка-curl)
- [Траблшутинг](#траблшутинг)

---

## Требования

### Для Docker-запуска
- Docker
- Docker Compose v2

### Для локального запуска
- Python 3.11+
- PostgreSQL 14+ (или через Docker)
- `pip`

---

## Конфигурация

Сервис читает настройки БД из окружения.

Поддерживаются два варианта:

### Вариант A (рекомендуется): `DB_*`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

### Вариант B: `DATABASE_URL`
Если задан `DATABASE_URL`, он имеет приоритет над `DB_*`.

Пример:
```
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/flaky_gate

```

### `.env` для локалки
В репозитории есть `.env.example`. Для локальной работы сделайте копию:

```bash
cp .env.example .env
```

---

## Быстрый старт в Docker

1. Создайте `.env`:

```bash
cp .env.example .env
```

2. Запустите сервис:

```bash
docker compose up --build
```

После старта:

* PostgreSQL будет поднят как сервис `db`
* API будет доступно на `http://localhost:8000`
* Миграции накатываются автоматически при старте контейнера API

Swagger UI:

* `http://localhost:8000/docs`

---

## Локальный запуск без Docker

### 1) Поднять PostgreSQL

Можно использовать локальную установку PostgreSQL или поднять только БД через Docker:

```bash
docker compose up -d db
```

### 2) Подготовить окружение Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Настроить env

Самый простой вариант — создать `.env` из примера:

```bash
cp .env.example .env
```

Если проект использует `python-dotenv` (рекомендуется), то `.env` подхватится автоматически при старте приложения.
Если нет — экспортируйте переменные вручную, например в bash/zsh:

```bash
set -a
source .env
set +a
```

### 4) Накатить миграции

```bash
alembic -c alembic.ini upgrade head
```

### 5) Запустить API

```bash
uvicorn app.main:app --reload
```

---

## Миграции

### Применить миграции

```bash
alembic -c alembic.ini upgrade head
```

### Откатить миграции

```bash
alembic -c alembic.ini downgrade -1
```

### Важное про `alembic.ini`

Поле `sqlalchemy.url` в `alembic.ini` может быть “пустышкой”: реальный URL берётся из env (см. раздел [Конфигурация](#конфигурация)).

---

## Тесты

Тесты используют реальную PostgreSQL (интеграционные).

### Вариант 1: БД в Docker, тесты локально

1. Поднимите БД:

```bash
docker compose up -d db
```

2. Настройте env (через `.env`):

```bash
cp .env.example .env
set -a
source .env
set +a
```

3. Запустите тесты:

```bash
pytest -q
```

### Вариант 2: всё в Docker (ручной подход)

Если хотите прогонять тесты внутри контейнера, обычно делается отдельный сервис `tests` в compose,
но это зависит от вашей инфраструктуры. Минимально — можно зайти в контейнер и запустить `pytest`.

---

## API: ручная проверка curl

### 1) Создать прогон

```bash
curl -X POST http://localhost:8000/runs \
  -H 'Content-Type: application/json' \
  -d '{"branch":"main"}'
```

Ответ:

```json
{"runId": 1}
```

### 2) Зарегистрировать тест-кейс (метаданные)

```bash
curl -X POST http://localhost:8000/cases \
  -H 'Content-Type: application/json' \
  -d '{"externalId":"T-1","name":"test_login","owner":"qa","isQuarantined":false}'
```

### 3) Добавить результаты тестов в прогон

```bash
curl -X POST http://localhost:8000/runs/1/results \
  -H 'Content-Type: application/json' \
  -d '[{"testExternalId":"T-1","status":"failed","durationMs":123,"errorMessage":"boom"}]'
```

### 4) Получить результат по индексу (0-based)

```bash
curl http://localhost:8000/runs/1/results/0
```

### 5) Получить flaky-статистику

Параметры:

* `window` — сколько последних прогонов анализировать (обязательный, > 0)
* `minFailRate` — минимальная доля фейлов (0..1)
* `owner` — фильтр по владельцу (опционально)
* `includeQuarantined` — включать ли quarantined тесты
* `limit`, `offset` — пагинация

Пример:

```bash
curl "http://localhost:8000/flaky?window=10&minFailRate=0.1&includeQuarantined=false&limit=50&offset=0"
```

---

## Траблшутинг

### “alembic: command not found”

Убедитесь, что зависимости установлены:

```bash
pip install -r requirements.txt
```

### “could not connect to server”

* Проверьте, что PostgreSQL запущен
* Проверьте переменные окружения (`DB_*` или `DATABASE_URL`)
* Если БД в Docker: `docker compose ps`, `docker compose logs db`

### “relation ... does not exist”

Значит миграции не применены:

```bash
alembic -c alembic.ini upgrade head
```

### Порт 5432/8000 занят

Измените проброс портов в `docker-compose.yml` или остановите конфликтующий процесс.

### При запуске api появляются ошибки вида ...

```bash
INFO:     127.0.0.1:port - "GET /livereload/#########/######### HTTP/1.1" 404 Not Found
```

Есть просмотр данного порта, возможно из-за расширения браузера. Можете либо не обращать внимания (ошибкой это не является), либо запускать браузер только в инкогнито.