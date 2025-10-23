#!/bin/bash

# Скрипт для пересборки и перезапуска бота

set -e

echo "🔄 Пересборка и перезапуск Nikta Oracle Bot..."

# Останавливаем контейнер
echo "1️⃣ Остановка контейнера..."
docker compose down

# Пересобираем образ
echo "2️⃣ Пересборка образа..."
docker compose build --no-cache

# Запускаем контейнер
echo "3️⃣ Запуск контейнера..."
docker compose up -d

echo "✅ Бот успешно пересобран и запущен!"
echo ""
echo "📊 Проверка статуса:"
docker compose ps

