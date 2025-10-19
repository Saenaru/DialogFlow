from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
import logging
import time
from dialogflow_utils import setup_logging, send_alert, get_dialogflow_response, check_required_env_vars, validate_dialogflow_config

logger = logging.getLogger(__name__)


def start(update, context):
    update.message.reply_text(
        "Привет!"
        "Задайте мне любой вопрос!"
    )


def handle_message(update, context):
    user_message = update.message.text
    user_id = update.message.from_user.id
    response_text, _ = get_dialogflow_response(user_message, str(user_id), platform='tg')
    update.message.reply_text(response_text)


def error_handler(update, context):
    error_msg = f"Ошибка Telegram Bot: {context.error}"
    logger.error(error_msg)
    send_alert(error_msg, "ERROR", "Telegram Bot")


def initialize_bot():
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    if not TELEGRAM_TOKEN:
        error_msg = "❌ TELEGRAM_BOT_TOKEN не найден в .env файле!"
        logger.error(error_msg)
        send_alert(error_msg, "CRITICAL", "Telegram Bot")
        return False

    try:
        logger.info("🤖 Telegram Бот запускается...")
        send_alert("Telegram Bot запускается...", "INFO", "Telegram Bot")
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        dp.add_error_handler(error_handler)
        updater.start_polling()
        time.sleep(2)
        bot_info = updater.bot.get_me()
        logger.info(f"✅ Бот успешно запущен! @{bot_info.username}")
        send_alert(f"Telegram Bot успешно запущен! @{bot_info.username}", "INFO", "Telegram Bot")
        return updater
    except Exception as e:
        error_msg = f"❌ Ошибка при запуске бота: {e}"
        logger.error(error_msg)
        send_alert(error_msg, "CRITICAL", "Telegram Bot")
        return None


def main():
    setup_logging()
    required_vars = ['TELEGRAM_BOT_TOKEN', 'MONITORING_BOT_TOKEN', 'ADMIN_CHAT_ID']
    if not check_required_env_vars(required_vars, "Telegram Bot"):
        return
    if not validate_dialogflow_config("Telegram Bot"):
        return

    updater = initialize_bot()
    if updater:
        updater.idle()


if __name__ == '__main__':
    main()