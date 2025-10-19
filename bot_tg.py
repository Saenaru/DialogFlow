from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
import logging
import time
from dialogflow_utils import setup_logging, send_alert, get_dialogflow_response
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def start(update, context):
    update.message.reply_text(
        "Привет!"
        "Задайте мне любой вопрос!"
    )


def handle_message(update, context):
    user_message = update.message.text
    user_id = update.message.from_user.id
    session_id = f"tg-{user_id}"
    response_text, _ = get_dialogflow_response(
        user_message, 
        session_id,
        context.bot_data['dialogflow_config'],
        platform='tg'
    )
    update.message.reply_text(response_text)


def error_handler(update, context):
    error_msg = f"Ошибка Telegram Bot: {context.error}"
    logger.error(error_msg)
    send_alert(error_msg, "ERROR", "Telegram Bot", context.bot_data['monitoring_config'])


def initialize_bot(telegram_token, dialogflow_config, monitoring_config):
    if not telegram_token:
        error_msg = "❌ TELEGRAM_BOT_TOKEN не найден в .env файле!"
        logger.error(error_msg)
        send_alert(error_msg, "CRITICAL", "Telegram Bot", monitoring_config)
        return False

    try:
        logger.info("🤖 Telegram Бот запускается...")
        send_alert("Telegram Bot запускается...", "INFO", "Telegram Bot", monitoring_config)
        updater = Updater(telegram_token, use_context=True)
        updater.dispatcher.bot_data['dialogflow_config'] = dialogflow_config
        updater.dispatcher.bot_data['monitoring_config'] = monitoring_config
        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        dp.add_error_handler(error_handler)
        updater.start_polling()
        time.sleep(2)
        bot_info = updater.bot.get_me()
        logger.info(f"✅ Бот успешно запущен! @{bot_info.username}")
        send_alert(f"Telegram Bot успешно запущен! @{bot_info.username}", "INFO", "Telegram Bot", monitoring_config)
        return updater
    except Exception as e:
        error_msg = f"❌ Ошибка при запуске бота: {e}"
        logger.error(error_msg)
        send_alert(error_msg, "CRITICAL", "Telegram Bot", monitoring_config)
        return None


def main():
    load_dotenv()
    setup_logging()
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    monitoring_token = os.getenv('MONITORING_BOT_TOKEN')
    admin_chat_id = os.getenv('ADMIN_CHAT_ID')
    dialogflow_project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
    dialogflow_key_file = os.getenv('DIALOGFLOW_KEY_FILE')
    
    if not all([telegram_token, monitoring_token, admin_chat_id, dialogflow_project_id, dialogflow_key_file]):
        error_msg = "❌ Отсутствуют одна или несколько обязательных переменных окружения"
        logger.error(error_msg)
        return
    
    if not os.path.exists(dialogflow_key_file):
        error_msg = f"❌ Файл {dialogflow_key_file} не найден!"
        logger.error(error_msg)
        return

    monitoring_config = {
        'token': monitoring_token,
        'admin_chat_id': admin_chat_id
    }

    dialogflow_config = {
        'project_id': dialogflow_project_id,
        'key_file': dialogflow_key_file
    }

    updater = initialize_bot(telegram_token, dialogflow_config, monitoring_config)
    if updater:
        updater.idle()


if __name__ == '__main__':
    main()
