#!/bin/bash

# Скрипт для запуска бота

cd "$(dirname "$0")"

# Активируем виртуальное окружение
source .venv/bin/activate

# Запускаем бота
echo "🚀 Запуск Nikta Oracle Bot..."
echo "Для остановки нажмите Ctrl+C"
echo ""

python bot.py



