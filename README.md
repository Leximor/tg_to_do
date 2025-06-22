# Telegram ToDo Bot

Telegram бот для управления задачами с Django backend и системой уведомлений.

## Настройка

### 1. Создание .env файла

Скопируйте `env.example` в `.env` и заполните необходимые переменные:

```bash
cp env.example .env
```

Отредактируйте `.env` файл:

```env
# Telegram Bot Token (получите у @BotFather)
BOT_TOKEN=your_telegram_bot_token_here

# Django Secret Key (сгенерируйте новый)
DJANGO_SECRET_KEY=your_django_secret_key_here

# Database
DB_NAME=todo_db
DB_USER=todo_user
DB_PASSWORD=todo_password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# API URL
API_URL=http://backend:8000/api/
```

### 2. Генерация Django Secret Key

Для генерации нового Django Secret Key выполните:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### 3. Запуск

```bash
# Сборка и запуск всех сервисов
docker-compose up --build -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## Архитектура

- **Bot** (aiogram) - Telegram интерфейс
- **Backend** (Django REST) - API для CRUD операций
- **Celery** - асинхронные уведомления о дедлайнах
- **PostgreSQL** - хранение данных
- **Redis** - очередь для Celery

## Функции

- ✅ Создание задач с категориями и дедлайнами
- ✅ Просмотр списка задач
- ✅ Автоматические уведомления о просроченных задачах
- ✅ Напоминания о приближающихся дедлайнах
- ✅ Возможность отключения уведомлений для конкретных задач
- ✅ Ежедневные сводки

## API Endpoints

- `GET /api/tasks/` - список задач
- `POST /api/tasks/` - создание задачи
- `PUT /api/tasks/{id}/` - обновление задачи
- `DELETE /api/tasks/{id}/` - удаление задачи
- `GET /api/categories/` - список категорий
- `GET /api/profiles/` - профили пользователей

## Возможности

- Создание задач с заголовком, описанием и дедлайном
- Выбор категории для каждой задачи
- Просмотр всех задач пользователя
- Правильное отображение даты с часовым поясом
- Полноценный REST API для управления задачами, категориями и пользователями
- **Система уведомлений через Telegram:**
  - Уведомления о просроченных задачах
  - Напоминания о приближающихся дедлайнах (за 1 час)
  - Ежедневные напоминания о задачах на завтра
  - Автоматическая отправка через Celery

## Запуск проекта

### 1. Настройка окружения

Создайте файл `.env` в корневой директории проекта:

```env
BOT_TOKEN=your_telegram_bot_token
API_URL=http://backend:8000/api/
```

### 2. Запуск с помощью скрипта

```bash
chmod +x setup.sh
./setup.sh
```

Этот скрипт:
- Запустит все сервисы через Docker Compose
- Выполнит миграции базы данных
- Создаст суперпользователя
- Создаст базовые категории

### 3. Ручной запуск

Если вы хотите запустить вручную:

```bash
# Запуск сервисов
docker-compose up -d

# Миграции
docker-compose exec backend python manage.py migrate

# Создание суперпользователя
docker-compose exec backend python manage.py createsuperuser --noinput

# Создание категорий
docker-compose exec backend python manage.py create_categories
```

## API Documentation

### Базовый URL
```
http://localhost:8000/api/
```

### Доступные эндпоинты

#### Задачи (Tasks)
- **GET** `/api/tasks/` - Получить список всех задач
- **POST** `/api/tasks/` - Создать новую задачу
- **GET** `/api/tasks/{id}/` - Получить конкретную задачу
- **PUT** `/api/tasks/{id}/` - Обновить задачу полностью
- **PATCH** `/api/tasks/{id}/` - Обновить задачу частично
- **DELETE** `/api/tasks/{id}/` - Удалить задачу

**Дополнительные действия:**
- **POST** `/api/tasks/{id}/complete/` - Отметить задачу как выполненную
- **POST** `/api/tasks/{id}/uncomplete/` - Отметить задачу как невыполненную
- **GET** `/api/tasks/overdue/` - Получить просроченные задачи
- **GET** `/api/tasks/completed/` - Получить выполненные задачи

**Фильтрация и поиск:**
- `?telegram_id=123456789` - Задачи конкретного пользователя
- `?is_completed=true` - Только выполненные задачи
- `?search=ключевое_слово` - Поиск по заголовку и описанию
- `?ordering=-created_at` - Сортировка по дате создания (новые сначала)

#### Категории (Categories)
- **GET** `/api/categories/` - Получить список всех категорий
- **POST** `/api/categories/` - Создать новую категорию
- **GET** `/api/categories/{id}/` - Получить конкретную категорию
- **PUT** `/api/categories/{id}/` - Обновить категорию полностью
- **PATCH** `/api/categories/{id}/` - Обновить категорию частично
- **DELETE** `/api/categories/{id}/` - Удалить категорию (только если в ней нет задач)

**Дополнительные действия:**
- **GET** `/api/categories/{id}/tasks/` - Получить все задачи в категории

**Фильтрация и поиск:**
- `?search=название` - Поиск по названию категории
- `?ordering=name` - Сортировка по названию

#### Пользователи (UserProfiles)
- **GET** `/api/profiles/` - Получить список всех профилей пользователей
- **POST** `/api/profiles/` - Создать новый профиль пользователя
- **GET** `/api/profiles/{id}/` - Получить конкретный профиль
- **PUT** `/api/profiles/{id}/` - Обновить профиль полностью
- **PATCH** `/api/profiles/{id}/` - Обновить профиль частично
- **DELETE** `/api/profiles/{id}/` - Удалить профиль пользователя

**Дополнительные действия:**
- **GET** `/api/profiles/{id}/tasks/` - Получить все задачи пользователя
- **GET** `/api/profiles/{id}/stats/` - Получить статистику пользователя

**Фильтрация и поиск:**
- `?search=username` - Поиск по username или имени
- `?ordering=telegram_username` - Сортировка по telegram username

### Работа с API через браузер

1. **Просмотр списков:**
   - Откройте `http://localhost:8000/api/tasks/` для просмотра всех задач
   - Откройте `http://localhost:8000/api/categories/` для просмотра всех категорий
   - Откройте `http://localhost:8000/api/profiles/` для просмотра всех пользователей

2. **Создание новых объектов:**
   - На странице списка нажмите кнопку "POST" в правом верхнем углу
   - Заполните форму и нажмите "POST"

3. **Редактирование и удаление:**
   - Перейдите на детальную страницу объекта: `/api/tasks/1/`, `/api/categories/2/`, `/api/profiles/3/`
   - На детальной странице появятся кнопки "PUT", "PATCH", "DELETE"

### Примеры запросов

#### Создание задачи
```bash
curl -X POST http://localhost:8000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Новая задача",
    "description": "Описание задачи",
    "user": 1,
    "categories": [1, 2],
    "due_date": "2025-06-25T10:00:00Z"
  }'
```

#### Получение задач пользователя
```bash
curl "http://localhost:8000/api/tasks/?telegram_id=123456789"
```

#### Обновление задачи
```bash
curl -X PATCH http://localhost:8000/api/tasks/1/ \
  -H "Content-Type: application/json" \
  -d '{"is_completed": true}'
```

#### Удаление категории
```bash
curl -X DELETE http://localhost:8000/api/categories/1/
```

### Форматы данных

#### Задача (Task)
```json
{
  "id": 1,
  "title": "Название задачи",
  "description": "Описание задачи",
  "created_at": "2025-06-22T13:14:17.123456Z",
  "due_date": "2025-06-25T10:00:00Z",
  "user": 1,
  "categories": [1, 2],
  "is_completed": false,
  "category_names": ["Работа", "Важное"],
  "user_info": {
    "id": 1,
    "telegram_id": "123456789",
    "telegram_username": "username"
  },
  "is_overdue": false
}
```

#### Категория (Category)
```json
{
  "id": 1,
  "name": "Название категории",
  "task_count": 5
}
```

#### Профиль пользователя (UserProfile)
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "tg_123456789",
    "email": "123456789@tg.local",
    "first_name": "Имя",
    "last_name": "Фамилия"
  },
  "telegram_id": "123456789",
  "telegram_username": "username",
  "task_count": 10
}
```

## Структура проекта

- `backend/` - Django REST API
- `bot/` - Telegram бот на aiogram
- `docker-compose.yml` - Конфигурация Docker Compose

## Использование бота

1. Найдите бота в Telegram по токену
2. Отправьте команду `/start`
3. Используйте кнопку "Добавить задачу" для создания новых задач
4. Выберите категорию из списка
5. Укажите дедлайн в формате YYYY-MM-DD HH:MM

## Формат отображения задач

Задачи отображаются в следующем формате:

```
2025-06-20 04:44
ЗАГОЛОВОК ЗАДАЧИ
Описание: ОПИСАНИЕ ЗАДАЧИ
Категории: Название категории
```

## Технические детали

- **Backend**: Django REST Framework
- **Bot**: aiogram 3.x
- **Database**: PostgreSQL
- **Cache**: Redis
- **Task Queue**: Celery
- **API**: Полноценный REST API с поддержкой CRUD операций
- **Фильтрация**: Поиск, сортировка, фильтрация по статусу
- **Пагинация**: Отключена для упрощения работы с ботом

## Система уведомлений

### Настройка

1. **Добавьте токен бота в настройки Django:**
   ```python
   # backend/todo_backend/settings.py
   BOT_TOKEN = 'your_actual_bot_token_here'
   ```

2. **Перезапустите сервисы:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Типы уведомлений

- **Просроченные задачи** - отправляются каждую минуту для задач, дедлайн которых уже прошел
- **Приближающиеся дедлайны** - отправляются каждые 5 минут для задач с дедлайном в течение часа
- **Ежедневные напоминания** - отправляются каждый день в 9:00 утра с задачами на завтра

### Тестирование уведомлений

```bash
# Тестовое уведомление
docker-compose exec backend python manage.py test_notifications --type test --telegram-id YOUR_TELEGRAM_ID

# Тест уведомлений о просроченных задачах
docker-compose exec backend python manage.py test_notifications --type due

# Тест уведомлений о приближающихся дедлайнах
docker-compose exec backend python manage.py test_notifications --type upcoming

# Тест ежедневных напоминаний
docker-compose exec backend python manage.py test_notifications --type daily
```

### Ручной запуск задач

```bash
# Запуск проверки просроченных задач
docker-compose exec backend python manage.py shell
>>> from tasks.tasks import check_due_tasks
>>> check_due_tasks.delay()

# Запуск проверки приближающихся задач
>>> from tasks.tasks import check_upcoming_tasks
>>> check_upcoming_tasks.delay()

# Запуск ежедневного напоминания
>>> from tasks.tasks import send_daily_reminder
>>> send_daily_reminder.delay()
```

### Мониторинг

Проверьте логи Celery для мониторинга работы уведомлений:
```bash
# Логи Celery worker
docker-compose logs celery

# Логи Celery beat (планировщик)
docker-compose logs celery-beat
```
