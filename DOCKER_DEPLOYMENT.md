# Развертывание бота с помощью Docker

## Предварительные требования

На сервере должны быть установлены:
- Docker (версия 20.10 или выше)
- Docker Compose (версия 2.0 или выше)

### Установка Docker на Ubuntu/Debian

```bash
# Обновляем пакеты
sudo apt-get update

# Устанавливаем необходимые пакеты
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# Добавляем официальный GPG ключ Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавляем репозиторий Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Устанавливаем Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Добавляем текущего пользователя в группу docker
sudo usermod -aG docker $USER

# Перелогиниваемся для применения изменений
newgrp docker
```

## Развертывание на сервере

### 1. Подготовка файлов

Скопируйте проект на сервер:

```bash
# Используя git
git clone <your-repository-url>
cd new-bot-for-conf

# Или используя scp
scp -r /path/to/new-bot-for-conf user@server:/path/to/destination/
```

### 2. Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
nano .env  # или используйте vim, vi и т.д.
```

Заполните необходимые значения:

```env
TELEGRAM_BOT_TOKEN=8358987328:AAGXZJ7grHfhIGG5z89mKdEy7tAYbeLy7Dk
API_URL=http://demo.nikta.ai/llm/api/run
```

### 3. Создание директории для логов

```bash
mkdir -p logs
```

### 4. Сборка и запуск контейнера

```bash
# Сборка образа
docker compose build

# Запуск в фоновом режиме
docker compose up -d
```

## Управление контейнером

### Просмотр логов

```bash
# Просмотр всех логов
docker compose logs

# Просмотр логов в реальном времени
docker compose logs -f

# Просмотр последних 100 строк
docker compose logs --tail=100
```

### Остановка бота

```bash
docker compose stop
```

### Запуск бота

```bash
docker compose start
```

### Перезапуск бота

```bash
docker compose restart
```

### Остановка и удаление контейнера

```bash
docker compose down
```

### Пересборка после изменений в коде

```bash
# Остановка, пересборка и запуск
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Проверка статуса

### Проверка запущенных контейнеров

```bash
docker compose ps
```

### Проверка использования ресурсов

```bash
docker stats nikta-oracle-bot
```

### Вход в контейнер для отладки

```bash
docker compose exec bot /bin/bash
```

## Автоматический запуск при перезагрузке сервера

Docker Compose с параметром `restart: unless-stopped` автоматически перезапустит контейнер при перезагрузке сервера.

Для проверки:

```bash
# Перезагрузка сервера
sudo reboot

# После перезагрузки проверьте статус
docker compose ps
```

## Обновление бота

### Обновление через Git

```bash
# Получаем последние изменения
git pull origin main

# Пересобираем и перезапускаем
docker compose down
docker compose build
docker compose up -d
```

### Ручное обновление файлов

```bash
# Загружаем новые файлы на сервер
scp bot.py user@server:/path/to/new-bot-for-conf/

# Пересобираем и перезапускаем
docker compose down
docker compose build
docker compose up -d
```

## Мониторинг и отладка

### Просмотр логов бота

```bash
# Логи из Docker
docker compose logs -f bot

# Логи из файла (если настроено)
tail -f logs/bot.log
```

### Проверка сетевого подключения из контейнера

```bash
docker compose exec bot ping -c 3 demo.nikta.ai
```

### Проверка переменных окружения

```bash
docker compose exec bot env | grep TELEGRAM
```

## Резервное копирование

### Создание резервной копии

```bash
# Создаем архив проекта
tar -czf nikta-bot-backup-$(date +%Y%m%d).tar.gz \
  bot.py \
  requirements.txt \
  Dockerfile \
  docker-compose.yml \
  .env \
  logs/

# Копируем на локальную машину
scp user@server:/path/to/nikta-bot-backup-*.tar.gz ./backups/
```

## Безопасность

### Рекомендации:

1. **Защита .env файла:**
   ```bash
   chmod 600 .env
   ```

2. **Регулярное обновление образов:**
   ```bash
   docker compose pull
   docker compose up -d
   ```

3. **Настройка firewall:**
   ```bash
   # Разрешаем только необходимые порты
   sudo ufw allow ssh
   sudo ufw enable
   ```

4. **Мониторинг логов на предмет ошибок:**
   ```bash
   docker compose logs | grep -i error
   ```

## Устранение неполадок

### Контейнер не запускается

```bash
# Проверяем логи
docker compose logs

# Проверяем конфигурацию
docker compose config

# Проверяем наличие .env файла
ls -la .env
```

### Бот не отвечает

```bash
# Проверяем, запущен ли контейнер
docker compose ps

# Проверяем логи на ошибки
docker compose logs --tail=50

# Перезапускаем бота
docker compose restart
```

### Проблемы с памятью

```bash
# Проверяем использование ресурсов
docker stats nikta-oracle-bot

# Увеличиваем лимит памяти в docker-compose.yml
# memory: 1024M
```

## Производительность

### Оптимизация образа

Образ уже оптимизирован:
- Используется slim-версия Python
- Удаляются кэши apt
- Используется многослойная структура для кэширования зависимостей

### Мониторинг производительности

```bash
# Установка ctop для мониторинга контейнеров
sudo wget https://github.com/bcicen/ctop/releases/download/v0.7.7/ctop-0.7.7-linux-amd64 -O /usr/local/bin/ctop
sudo chmod +x /usr/local/bin/ctop

# Запуск мониторинга
ctop
```

## Дополнительная информация

- Логи контейнера ротируются автоматически (максимум 3 файла по 10MB)
- Контейнер запускается от непривилегированного пользователя для безопасности
- Настроены ограничения по CPU и памяти для предотвращения перегрузки сервера

