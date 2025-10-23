#!/bin/bash

# Скрипт для запуска бота в Docker

set -e

echo "🚀 Запуск Nikta Oracle Bot в Docker..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Ошибка: файл .env не найден!"
    echo "📝 Создайте файл .env на основе .env.example"
    exit 1
fi

# Создаём директорию для логов
mkdir -p logs

# Запускаем контейнер
docker compose up -d

echo "✅ Бот успешно запущен!"
echo ""
echo "📊 Полезные команды:"
echo "  docker compose logs -f          # Просмотр логов в реальном времени"
echo "  docker compose ps               # Статус контейнера"
echo "  docker compose stop             # Остановка бота"
echo "  docker compose restart          # Перезапуск бота"
echo "  docker compose down             # Остановка и удаление контейнера"

