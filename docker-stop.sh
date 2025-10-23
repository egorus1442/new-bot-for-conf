#!/bin/bash

# Скрипт для остановки бота в Docker

set -e

echo "🛑 Остановка Nikta Oracle Bot..."

docker compose stop

echo "✅ Бот успешно остановлен!"

