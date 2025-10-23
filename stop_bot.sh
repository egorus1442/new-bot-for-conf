#!/bin/bash

# Скрипт для остановки бота

echo "🛑 Остановка бота..."

# Находим и останавливаем все процессы бота
pkill -9 -f "python.*bot.py"
pkill -9 -f "start_bot.sh"

sleep 2

# Проверяем, остались ли процессы
if pgrep -f "python.*bot.py" > /dev/null; then
    echo "⚠️  Некоторые процессы все еще работают"
else
    echo "✅ Все процессы бота остановлены"
fi

