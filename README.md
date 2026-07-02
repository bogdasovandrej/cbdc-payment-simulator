# Симулятор оплаты по QR-коду на базе API платформы цифрового рубля ЦБ РФ

**Живая демка:** https://cbdc-payment-simulator.onrender.com
(бесплатный хостинг: после простоя сервис просыпается ~минуту)

Backend-сервис (MVP), моделирующий полный цикл приёма платежа в цифровых рублях:
создание платежа → генерация QR-кода → асинхронная обработка во «внешней» системе →
зачисление средств на кошелёк и запись транзакции.

Настоящее API платформы цифрового рубля недоступно публично, поэтому его роль
выполняет встроенный **Mock CBDC API** — отдельный модуль, который имитирует
поведение внешней системы: случайные сетевые задержки, вероятность отказа
платежа и фоновую смену статусов.

У сервиса есть **веб-интерфейс** (одностраничный, vanilla JS поверх того же
API): регистрация и вход, баланс кошелька, выставление счёта, QR-код,
статусы платежей в реальном времени и история операций. Открывается на
корневом адресе сервера.

## Стек

| Технология | Назначение |
|---|---|
| Python 3.12 | язык |
| FastAPI | HTTP API, Swagger/OpenAPI из коробки |
| SQLAlchemy 2.0 | ORM |
| Alembic | миграции схемы БД |
| PostgreSQL | основная БД |
| Pydantic v2 | DTO и валидация запросов/ответов |
| PyJWT + passlib (bcrypt) | JWT-аутентификация и хеширование паролей |
| qrcode | генерация QR-кодов (PNG) |
| pytest + httpx | тесты |
| Docker + Docker Compose | контейнеризация и запуск одной командой |

## Архитектура

Классическая слоистая архитектура: роутеры не содержат бизнес-логики,
сервисы не пишут SQL, репозитории не знают про HTTP.

```
app/
├── main.py            # приложение FastAPI, глобальные exception handlers
├── core/              # конфигурация (pydantic-settings), JWT, исключения
├── db/                # engine, фабрика сессий, декларативная база
├── models/            # SQLAlchemy-модели: User, Wallet, Payment, QRCode, Transaction
├── schemas/           # Pydantic DTO — модели БД наружу не отдаются
├── repositories/      # доступ к данным (SQL-запросы)
├── services/          # бизнес-логика: auth, payments, QR, payment_processor
├── api/               # роутеры FastAPI + зависимости (get_db, get_current_user)
├── mock_cbdc/         # имитация внешнего API цифрового рубля
└── utils/             # генерация QR, работа с датами
alembic/               # миграции
tests/                 # pytest-тесты (SQLite, без Docker)
analytics/             # бонус: SQL-аналитика и pandas-отчёт по платежам
```

## Жизненный цикл платежа

```
клиент                 наш backend                Mock CBDC (внешняя система)
  │  POST /api/payments     │                            │
  ├─────────────────────────►  Payment: CREATED          │
  │                         │  QRCode: сгенерирован      │
  │                         ├────── submit_payment ─────►│  ACCEPTED
  │  201 {status: CREATED}  │                            │
  ◄─────────────────────────┤        (фоновая задача)    │
  │                         │◄────── PROCESSING ─────────┤  задержка сети
  │                         │◄────── PAID | FAILED ──────┤  вероятность отказа
  │                         │  при PAID: баланс += сумма │
  │  GET /api/payments/{id} │  + запись Transaction      │
  ├─────────────────────────►                            │
  │  200 {status: PAID}     │                            │
```

Статусы: `CREATED → PROCESSING → PAID | FAILED`. Переходы контролируются
строго (нельзя, например, оплатить уже проваленный платёж), зачисление на
баланс и создание транзакции происходят в одной транзакции БД.

## Запуск

### Docker Compose (рекомендуемый способ)

```bash
docker-compose up --build
```

Поднимаются PostgreSQL и приложение; миграции Alembic применяются автоматически
при старте контейнера. После запуска:

* Веб-интерфейс: http://localhost:8000
* Swagger UI: http://localhost:8000/docs
* ReDoc: http://localhost:8000/redoc
* Health check: http://localhost:8000/health

### Локально без Docker (самый быстрый способ)

Не требует ни Docker, ни PostgreSQL — используется SQLite:

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python run_local.py
```

Скрипт сам применит миграции и запустит сервер на http://127.0.0.1:8000.

### Локально с PostgreSQL

Нужен запущенный PostgreSQL (можно поднять только БД: `docker-compose up db`).

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env        # и при необходимости отредактировать
alembic upgrade head
uvicorn app.main:app --reload
```

### Тесты

Тесты не требуют Docker и PostgreSQL — используют SQLite, задержки мок-сервиса
отключены, вероятность отказа управляется из теста.

```bash
pytest
```

## API

Все защищённые эндпоинты требуют заголовок `Authorization: Bearer <access_token>`.

### Auth

| Метод | Путь | Описание | Ошибки |
|---|---|---|---|
| POST | `/api/auth/register` | регистрация (создаёт пользователя и кошелёк) | 409, 422 |
| POST | `/api/auth/login` | вход, выдаёт access + refresh токены | 401 |
| POST | `/api/auth/refresh` | новая пара токенов по refresh-токену | 401 |

### User

| Метод | Путь | Описание | Ошибки |
|---|---|---|---|
| GET | `/api/user/profile` | профиль текущего пользователя | 401 |
| GET | `/api/user/balance` | баланс кошелька | 401 |
| GET | `/api/user/transactions` | история операций | 401 |

### Payments

| Метод | Путь | Описание | Ошибки |
|---|---|---|---|
| POST | `/api/payments` | создать платёж (статус CREATED) | 401, 422 |
| GET | `/api/payments` | список платежей (пагинация limit/offset) | 401 |
| GET | `/api/payments/{id}` | статус платежа | 401, 404 |

### QR

| Метод | Путь | Описание | Ошибки |
|---|---|---|---|
| GET | `/api/qr/{payment_id}` | payload и срок действия QR-кода | 401, 404, 410 |
| GET | `/api/qr/{payment_id}/image` | QR-код как PNG | 401, 404, 410 |

### Mock CBDC API (имитация внешней системы)

| Метод | Путь | Описание |
|---|---|---|
| POST | `/mock/pay` | принять платёж во «внешней» системе |
| GET | `/mock/status/{id}` | статус операции во «внешней» системе |

### Формат ошибок

Все ошибки возвращаются в едином виде:

```json
{
  "error": {
    "code": "not_found",
    "message": "Платёж не найден"
  }
}
```

## Пример сценария (curl)

```bash
# 1. Регистрация
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# 2. Логин
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
# → {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}

# 3. Создание платежа (подставьте свой access_token)
curl -X POST http://localhost:8000/api/payments \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"amount": "1500.00"}'
# → {"id": 1, "status": "CREATED", ...}

# 4. QR-код платежа (PNG можно открыть в браузере)
curl http://localhost:8000/api/qr/1 -H "Authorization: Bearer <ACCESS_TOKEN>"

# 5. Через пару секунд — статус платежа
curl http://localhost:8000/api/payments/1 -H "Authorization: Bearer <ACCESS_TOKEN>"
# → {"id": 1, "status": "PAID", ...}   (или FAILED — мок эмулирует отказы)

# 6. Баланс и история операций
curl http://localhost:8000/api/user/balance -H "Authorization: Bearer <ACCESS_TOKEN>"
curl http://localhost:8000/api/user/transactions -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Деплой (бесплатно, Render.com)

В репозитории есть [`render.yaml`](render.yaml) — blueprint для Render:

1. Зарегистрируйтесь на [render.com](https://render.com) (вход через GitHub).
2. **New +** → **Blueprint** → выберите этот репозиторий → **Apply**.
3. Через несколько минут сервис будет доступен по адресу вида
   `https://cbdc-payment-simulator.onrender.com`.

Особенности бесплатного тарифа: сервис «засыпает» после 15 минут без
трафика (первый запрос будит его за ~минуту), демо-база — SQLite,
данные сбрасываются при перезапуске.

## Настройки (переменные окружения)

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://cbdc:cbdc@localhost:5432/cbdc` | строка подключения к БД |
| `JWT_SECRET_KEY` | `change-me-in-production` | секрет подписи JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | срок жизни access-токена |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | срок жизни refresh-токена |
| `QR_TTL_MINUTES` | `15` | срок действия QR-кода |
| `MOCK_MIN_DELAY_SECONDS` | `1.0` | мин. задержка «сети» в моке |
| `MOCK_MAX_DELAY_SECONDS` | `3.0` | макс. задержка «сети» в моке |
| `MOCK_FAIL_PROBABILITY` | `0.2` | вероятность отказа платежа |

## Скриншоты

<!-- Место под скриншоты Swagger UI -->
<!-- ![Swagger UI](docs/swagger.png) -->
<!-- ![Создание платежа](docs/create-payment.png) -->

## Бонус: SQL-аналитика по платежам

В каталоге [`analytics/`](analytics/) — аналитический трек поверх того же датасета:

* [`queries.sql`](analytics/queries.sql) — распределение по статусам, конверсия
  в успешные платежи, среднее время обработки, динамика по дням, топ
  пользователей, сверка баланса с транзакциями (проверка целостности);
* [`payments_report.py`](analytics/payments_report.py) — тот же отчёт на pandas
  (`pip install pandas`, затем `python analytics/payments_report.py` при
  поднятой БД).

## Ограничения MVP

* Mock CBDC хранит реестр операций в памяти процесса — при перезапуске
  приложения «внешняя» история теряется (платежи в БД остаются).
* Один кошелёк на пользователя, только входящие платежи (DEPOSIT).
* Refresh-токены не отзываются (нет чёрного списка) — вне рамок MVP.
