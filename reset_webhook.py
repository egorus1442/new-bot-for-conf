#!/usr/bin/env python3
"""Скрипт для сброса webhook и очистки состояния бота."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN не найден в .env")
    exit(1)

# Удаляем webhook
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
params = {"drop_pending_updates": True}

print("🔄 Удаление webhook и очистка обновлений...")
response = requests.post(url, params=params)

if response.status_code == 200:
    print("✅ Webhook удален и обновления очищены")
    print(response.json())
else:
    print(f"❌ Ошибка: {response.status_code}")
    print(response.text)

