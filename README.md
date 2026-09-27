# DATAM

Интернет-магазин одежды с личным кабинетом и админкой. Фронтенд написан на React и Vite, API — на FastAPI, данные хранятся в PostgreSQL. Весь проект запускается через Docker Compose.

| Сервис | Адрес |
| --- | --- |
| Магазин | [localhost](http://localhost) |
| Админка | [localhost/admin](http://localhost/admin) |
| pgAdmin | [localhost/pgadmin](http://localhost/pgadmin) |
| Документация API | [localhost/docs](http://localhost/docs) |

## Быстрый запуск

Нужны Docker Compose и `make`.

```bash
cp .env.example .env
```

В `.env` задайте свои значения для `SECRET_KEY`, `POSTGRES_PASSWORD` и `PGADMIN_DEFAULT_PASSWORD`. Для ключа и пароля PostgreSQL подойдут длинные случайные hex-строки: `openssl rand -hex 32`. Пароль PostgreSQL должен быть безопасным для URL, поскольку Compose вставляет его в `DATABASE_URL`.

```bash
make up
make seed
```

`make up` собирает и запускает контейнеры; миграции применяются при старте backend. `make seed` добавляет демо-каталог в текущую базу `datam`. Команда идемпотентна: повторный запуск не создаёт дубликаты. Автоматического seed при запуске нет.

## Доступ к админке

На новой базе сначала зарегистрируйте пользователя в магазине. Затем откройте pgAdmin и выполните в Query Tool для базы `datam`:

```sql
UPDATE users SET role = 'admin' WHERE email = 'you@example.com';
```

Подставьте email зарегистрированного пользователя и войдите под ним на [localhost/admin](http://localhost/admin). В админке доступны товары, категории, пользователи и заказы. Заказы можно искать, фильтровать, менять их статус и редактировать данные доставки до отправки. Отмена до отправки возвращает товары на склад.

Для входа в pgAdmin используйте `PGADMIN_DEFAULT_EMAIL` и `PGADMIN_DEFAULT_PASSWORD` из `.env`. Сервер DATAM уже добавлен; при подключении к нему введите `POSTGRES_PASSWORD`.

## Команды

| Команда | Что делает |
| --- | --- |
| `make up` | Собирает и запускает проект |
| `make down` | Останавливает контейнеры, сохраняя данные |
| `make restart` | Перезапускает сервисы |
| `make ps` | Показывает состояние контейнеров |
| `make logs` | Открывает логи |
| `make shell` | Открывает shell в backend |
| `make migrate` | Применяет миграции вручную |
| `make seed` | Добавляет демо-каталог в текущую базу |
| `make build` | Пересобирает образы |
| `make clean` | Удаляет локальные кеши Python и инструментов |
| `make reset` | Удаляет контейнеры и **все тома проекта**, включая базу данных |

Полный список: `make help`.

## Как устроен проект

| Путь | Содержимое |
| --- | --- |
| `frontend/src/app` | Маршруты и настройка приложения |
| `frontend/src/pages/admin` | Страницы админки |
| `frontend/src/features/admin` | Запросы и типы админского API |
| `frontend/src/entities` | Модели и API товаров, заказов, пользователей и других сущностей |
| `backend/app/routes` | Публичные и админские HTTP-маршруты |
| `backend/app/services` | Логика каталога, заказов и аккаунтов |
| `backend/database/migrations` | Миграции Alembic |
| `backend/seed.py` | Демо-каталог |

Админские маршруты API: `/api/admin/catalog/products`, `/api/admin/catalog/categories`, `/api/admin/users` и `/api/admin/orders`. Страницы фронтенда используют адреса `/admin/...`.

## Данные и сеть

PostgreSQL работает в отдельной базе `datam`. Данные базы сохраняются в томе `postgres-data`, настройки pgAdmin — в `pgadmin-data`, загруженные файлы — в `backend-data`. Порты PostgreSQL и backend не опубликованы наружу; Nginx на `127.0.0.1:80` передаёт `/api` и `/media` в backend, а `/pgadmin` — в pgAdmin.
