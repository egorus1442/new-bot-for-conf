#!/bin/bash

# Скрипт для проверки статуса бота

echo "📊 Статус Nikta Oracle Bot"
echo "=========================="
echo ""

echo "🐳 Статус контейнера:"
docker compose ps
echo ""

echo "💾 Использование ресурсов:"
docker stats nikta-oracle-bot --no-stream
echo ""

echo "📝 Последние 10 строк логов:"
docker compose logs --tail=10

