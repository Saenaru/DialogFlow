# Чат-боты с интеграцией Dialogflow

Этот проект включает в себя двух чат-ботов для Telegram и ВКонтакте с интеллектуальной обработкой сообщений через Dialogflow и системой мониторинга.

## Функциональность

###  Telegram Бот

-   **Интеграция с Dialogflow** для обработки естественного языка
    
-   **Команда `/start`** для приветствия пользователей
    
-   Обработка текстовых сообщений
    
-   **Система оповещений** об ошибках в реальном времени
    

###  VK Бот

-   **Интеграция с Dialogflow**
    
-   **Автоматическое определение fallback-интентов** - бот не отвечает на непонятные сообщения
    
-   **Приветственное сообщение** при старте
    
-   Отправка сообщений только при успешном распознавании интента
    

### Мониторинг

-   **Отправка уведомлений** в Telegram-канал администратора
    
-   **Оповещения о запуске/остановке** ботов
    
-   **Уведомления об ошибках** с детализацией
    
-   Поддержка разных **уровней оповещений** (INFO, ERROR, CRITICAL)
    

## Установка и настройка

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```
### 2. Настройка Dialogflow

1.  Создайте проект в [Google Cloud Console](https://console.cloud.google.com/)
    
2.  Активируйте **Dialogflow API**
    
3.  Создайте **сервисный аккаунт** и скачайте JSON-ключ
    
4.  Сохраните файл ключа как `***.json` в корне проекта
    

### 3. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

env

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# VK Bot
VK_GROUP_TOKEN=your_vk_group_token_here
VK_GROUP_ID=your_vk_group_id_here

# Dialogflow
DIALOGFLOW_PROJECT_ID=your_dialogflow_project_id_here

# Monitoring
MONITORING_BOT_TOKEN=your_monitoring_bot_token_here
ADMIN_CHAT_ID=your_admin_chat_id_here

### 4. Получение токенов

**🤖 Telegram Bot:**

-   Напишите [@BotFather](https://t.me/BotFather) в Telegram
    
-   Используйте команду `/newbot`
    
-   Следуйте инструкциям и сохраните полученный токен
    

**👥 VK Bot:**

-   Создайте сообщество ВКонтакте
    
-   Перейдите в "Управление" → "Работа с API"
    
-   Создайте ключ доступа с необходимыми правами
    
-   Включите Long Poll API в настройках
    

**Monitoring Bot:**

-   Создайте отдельного Telegram бота через @BotFather
    
-   Узнайте ваш chat_id с помощью бота [@userinfobot](https://t.me/userinfobot)
    

## Запуск

### Запуск Telegram бота:

bash

python bot_tg.py

### Запуск VK бота:

bash

python bot_vk.py

### Импорт интентов в Dialogflow:

```bash
python DialogFlowscript.py
```

## Система мониторинга

Боты отправляют уведомления в Telegram-канал администратора:

-   ✅ **INFO** - Успешный запуск ботов, статус работы
    
-   🔔 **WARNING** - Предупреждения и не критичные ошибки
    
-   ❌ **ERROR** - Ошибки в работе ботов или Dialogflow
    
-   🚨 **CRITICAL** - Критические сбои, требующие немедленного внимания
    

## Скрипт импорта интентов

`DialogFlowscript.py` предоставляет функциональность для:

-   **Предпросмотра** интентов перед импортом
    
-   **Удаления** существующих интентов (кроме стандартных)
    
-   **Создания** новых интентов на основе JSON данных
    
-   **Валидации** данных и обработки ошибок
    

```bash
python DialogFlowscript.py
```
Скрипт запросит подтверждение перед выполнением деструктивных операций.

## Демонстрация работы
![tgbot](https://github.com/user-attachments/assets/5e6f4247-12a1-49ce-ba4d-a8060f4787d8)
![vkbot](https://github.com/user-attachments/assets/a6c3fd89-fa8f-4e80-8f5e-601a2bbe17d1)


