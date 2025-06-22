#!/bin/bash

echo "Starting the project..."

# Запускаем docker-compose
docker-compose up -d

# Ждем немного, чтобы сервисы запустились
echo "Waiting for services to start..."
sleep 10

# Выполняем миграции
echo "Running migrations..."
docker-compose exec backend python manage.py migrate

# Создаем суперпользователя (если не существует)
echo "Creating superuser..."
docker-compose exec backend python manage.py createsuperuser --noinput || true

# Создаем категории
echo "Creating categories..."
docker-compose exec backend python manage.py create_categories

echo "Setup completed!"
echo "You can now use the bot."
