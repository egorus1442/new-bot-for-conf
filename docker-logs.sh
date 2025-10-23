#!/bin/bash

# Скрипт для просмотра логов бота

echo "📋 Просмотр логов Nikta Oracle Bot..."
echo "Нажмите Ctrl+C для выхода"
echo ""

docker compose logs -f --tail=100

