# Система управления командой

**Веб-приложение для управления командами, задачами, встречами и оценкой сотрудников.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-336791?style=flat&logo=postgresql)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red?style=flat)](https://www.sqlalchemy.org/)

## 📋 Описание

Система предназначена для эффективного управления командной работой. Включает в себя:

- 👥 **Управление командами** - создание команд, приглашение участников, управление ролями
- ✅ **Управление задачами** - создание, назначение, отслеживание статуса и приоритета задач
- 📅 **Календарь и встречи** - планирование встреч, управление участниками
- 💬 **Комментарии** - обсуждение задач внутри команды
- ⭐ **Оценка сотрудников** - система оценивания работы участников команды
- 🔐 **Аутентификация и авторизация** - безопасный доступ с разделением прав
- 🎛️ **Админ-панель** - административное управление системой

## 🏗️ Архитектура

Проект построен на современной архитектуре с разделением ответственности:

```
src/
├── admin/              # Админ-панель (SQLAdmin)
├── alembic/            # Миграции базы данных
├── api/                # API endpoints
│   ├── frontend/       # Frontend роутеры (модульная структура)
│   └── [REST API]      # REST API endpoints
├── core/               # Ядро приложения (config, database, auth)
├── crud/               # CRUD операции с БД
├── models/             # SQLAlchemy модели
├── schemas/            # Pydantic схемы
├── services/           # Бизнес-логика
├── utils/              # Вспомогательные функции
├── frontend_templates/ # Jinja2 шаблоны
└── static/             # Статические файлы (CSS, JS, images)
```

### Слои приложения

1. **API Layer** (`api/`) - обработка HTTP запросов, валидация входных данных
2. **Service Layer** (`services/`) - бизнес-логика приложения
3. **CRUD Layer** (`crud/`) - операции с базой данных
4. **Models** (`models/`) - ORM модели SQLAlchemy
5. **Schemas** (`schemas/`) - Pydantic схемы для валидации

## 🚀 Технологии

### Backend
- **FastAPI** - современный веб-фреймворк для Python
- **SQLAlchemy 2.0** - ORM с асинхронной поддержкой
- **Alembic** - миграции базы данных
- **Pydantic** - валидация данных
- **asyncpg** - асинхронный драйвер PostgreSQL
- **Passlib + Bcrypt** - хеширование паролей
- **Python-JOSE** - JWT токены

### Frontend
- **Jinja2** - шаблонизатор
- **HTML/CSS/JavaScript** - клиентская часть

### База данных
- **PostgreSQL 14** - реляционная база данных

### DevOps
- **Docker & Docker Compose** - контейнеризация
- **Uvicorn** - ASGI сервер

## 📦 Установка и запуск

### Требования

- Python 3.10+
- PostgreSQL 14+
- Docker & Docker Compose (для запуска через Docker)

### Способ 1: Запуск через Docker (рекомендуется)

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd final
```

2. **Создайте файл `.env` в папке `src/`:**
```bash
cp .env.example src/.env
```

3. **Отредактируйте `src/.env`:**
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/effectivedb
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
```

4. **Запустите контейнеры:**
```bash
cd infra
docker-compose up -d
```

5. **Примените миграции:**
```bash
docker exec -it fastapi_app alembic upgrade head
```

6. **Приложение доступно:**
- Frontend: http://localhost:8000
- API документация: http://localhost:8000/docs
- Админ-панель: http://localhost:8000/admin

### Способ 2: Локальный запуск

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd final
```

2. **Создайте виртуальное окружение:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Установите зависимости:**
```bash
cd src
pip install -r requirements.txt
```

4. **Создайте PostgreSQL базу данных:**
```bash
# Через psql
createdb team_management

# Или через SQL
CREATE DATABASE team_management;
```

5. **Создайте файл `.env`:**
```bash
cp .env.example .env
```

6. **Отредактируйте `.env`:**
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/team_management
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=development
```

7. **Примените миграции:**
```bash
cd src
alembic upgrade head
```

8. **Запустите приложение:**
```bash
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

9. **Приложение доступно:**
- Frontend: http://localhost:8000
- API документация: http://localhost:8000/docs
- Админ-панель: http://localhost:8000/admin

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|-----------|----------|----------------------|
| `DATABASE_URL` | URL подключения к PostgreSQL | `postgresql+asyncpg://user:password@localhost:5432/team_management` |
| `SECRET_KEY` | Секретный ключ для JWT и сессий | `fallbacksecret` (⚠️ измените в продакшене!) |
| `ALGORITHM` | Алгоритм шифрования JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена (минуты) | `30` |
| `ENVIRONMENT` | Окружение (development/production) | `development` |

### Суперпользователь

При первом запуске автоматически создается суперпользователь:

- **Email:** `admin@example.com`
- **Пароль:** `admin123`

⚠️ **Измените пароль сразу после первого входа!**

Настройки суперпользователя находятся в `src/utils/init_superuser.py`.

## 📚 API Документация

### Swagger UI
Интерактивная документация доступна по адресу:
```
http://localhost:8000/docs
```

### ReDoc
Альтернативная документация:
```
http://localhost:8000/redoc
```

### Основные эндпоинты

#### Аутентификация
- `POST /api/auth/register` - регистрация нового пользователя
- `POST /api/auth/login` - вход в систему
- `POST /api/auth/logout` - выход из системы

#### Команды
- `GET /api/teams` - список команд пользователя
- `POST /api/teams` - создание команды
- `GET /api/teams/{id}` - получение команды
- `PUT /api/teams/{id}` - обновление команды
- `DELETE /api/teams/{id}` - удаление команды
- `POST /api/teams/{id}/join` - присоединение к команде

#### Задачи
- `GET /api/tasks` - список задач
- `POST /api/tasks` - создание задачи
- `GET /api/tasks/{id}` - получение задачи
- `PUT /api/tasks/{id}` - обновление задачи
- `DELETE /api/tasks/{id}` - удаление задачи

#### Встречи
- `GET /api/meetings` - список встреч
- `POST /api/meetings` - создание встречи
- `GET /api/meetings/{id}` - получение встречи
- `PUT /api/meetings/{id}` - обновление встречи
- `DELETE /api/meetings/{id}` - удаление встречи

#### Комментарии
- `GET /api/comments` - список комментариев
- `POST /api/comments` - создание комментария
- `PUT /api/comments/{id}` - обновление комментария
- `DELETE /api/comments/{id}` - удаление комментария

#### Оценки
- `GET /api/evaluations` - список оценок
- `POST /api/evaluations` - создание оценки
- `GET /api/evaluations/{id}` - получение оценки

#### Календарь
- `GET /api/calendar/month` - календарь на месяц
- `GET /api/calendar/day` - задачи и встречи на день

## 🗄️ База данных

### Модели

- **User** - пользователи системы
- **Team** - команды
- **Task** - задачи с статусами и приоритетами
- **Meeting** - встречи
- **Comment** - комментарии к задачам
- **Evaluation** - оценки пользователей

### Миграции

Создание новой миграции:
```bash
cd src
alembic revision --autogenerate -m "описание изменений"
```

Применение миграций:
```bash
alembic upgrade head
```

Откат миграции:
```bash
alembic downgrade -1
```

## 🧪 Тестирование

```bash
cd tests
pytest
```

Запуск с покрытием:
```bash
pytest --cov=src --cov-report=html
```

## 🎨 Особенности реализации

### 1. Модульная архитектура Frontend
Frontend разделен на отдельные модули по доменам:
- `auth.py` - аутентификация и регистрация
- `dashboard.py` - главная страница
- `tasks.py` - управление задачами
- `teams.py` - управление командами
- `meetings.py` - управление встречами
- `profile.py` - профиль пользователя

### 2. Service Layer
Бизнес-логика вынесена в отдельный слой сервисов:
- Централизованная валидация
- Переиспользуемая логика
- Легкое тестирование

### 3. CRUD отделен от Utils
CRUD операции находятся в отдельной папке `crud/`, а вспомогательные функции в `utils/`.

### 4. Dependency Injection
Используется паттерн DI для аутентификации и доступа к БД

### 5. Унифицированная обработка форм
Все ошибки форм обрабатываются единообразно через `form_helpers.py`

### 6. Комплексная валидация
Все данные валидируются через функции из `utils/validation.py`:
- Форматы (email, UUID, datetime)
- Права доступа
- Бизнес-правила

## 🔐 Безопасность

- **Пароли** хешируются с помощью bcrypt
- **JWT токены** для API аутентификации
- **Сессии** для frontend с защитой от CSRF
- **Валидация** всех входных данных через Pydantic
- **SQL Injection** защита через SQLAlchemy ORM
- **Разделение прав** - владельцы команд, участники, администраторы

## 🐛 Отладка

### Debug endpoints

```bash
# Проверка здоровья приложения
GET /health
```

## 📈 Производительность

- **Асинхронная работа** с БД через asyncpg
- **Connection pooling** через SQLAlchemy
- **Eager loading** для избежания N+1 проблемы
- **Индексы** на часто запрашиваемых полях

---

**Для вопросов и предложений создавайте Issues в репозитории.**
