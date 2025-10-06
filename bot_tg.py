from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv
from google.cloud import dialogflow
from google.oauth2 import service_account
import os
import logging
import requests
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
DIALOGFLOW_KEY_FILE = "newagent-ucxn-8332c4ae589a.json"
MONITORING_BOT_TOKEN = os.getenv('MONITORING_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')


def send_alert(message, level="ERROR", bot_name="Telegram Bot"):
    if not MONITORING_BOT_TOKEN or not ADMIN_CHAT_ID:
        return

    try:
        formatted_message = f"🚨 *{level} Alert - {bot_name}*\n\n{message}"
        url = f"https://api.telegram.org/bot{MONITORING_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': ADMIN_CHAT_ID,
            'text': formatted_message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Alert sent to monitoring bot: {level}")

    except Exception as e:
        logger.error(f"Failed to send alert to monitoring bot: {e}")


def get_dialogflow_response(text, session_id, language_code='ru'):
    try:
        credentials = service_account.Credentials.from_service_account_file(DIALOGFLOW_KEY_FILE)
        session_client = dialogflow.SessionsClient(credentials=credentials)
        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)
        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        response = session_client.detect_intent(
            session=session,
            query_input=query_input
        )
        return response.query_result.fulfillment_text

    except Exception as e:
        error_msg = f"Ошибка Dialogflow: {e}"
        logger.error(error_msg)
        send_alert(error_msg, "ERROR", "Telegram Bot")
        return "Извините, произошла ошибка при обработке запроса."


def start(update, context):
    update.message.reply_text(
        "Привет! Я умный бот с интеграцией Dialogflow. "
        "Задайте мне любой вопрос!"
    )


def handle_message(update, context):
    user_message = update.message.text
    user_id = update.message.from_user.id
    response_text = get_dialogflow_response(user_message, str(user_id))
    update.message.reply_text(response_text)


def error_handler(update, context):
    error_msg = f"Ошибка Telegram Bot: {context.error}"
    logger.error(error_msg)
    send_alert(error_msg, "ERROR", "Telegram Bot")


def main():
    if not TELEGRAM_TOKEN:
        error_msg = "❌ TELEGRAM_BOT_TOKEN не найден в .env файле!"
        logger.error(error_msg)
        send_alert(error_msg, "CRITICAL", "Telegram Bot")
        return

    if not DIALOGFLOW_PROJECT_ID:
        error_msg = "❌ DIALOGFLOW_PROJECT_ID не найден в .env файле!"
        logger.error(error_msg)
        send_alert(error_msg, "CRITICAL", "Telegram Bot")
        return

    if not os.path.exists(DIALOGFLOW_KEY_FILE):
        error_msg = f"❌ Файл {DIALOGFLOW_KEY_FILE} не найден!"
        logger.error(error_msg)
        send_alert(error_msg, "CRITICAL", "Telegram Bot")
        return

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
        updater.idle()

    except Exception as e:
        error_msg = f"❌ Ошибка при запуске бота: {e}"
        logger.error(error_msg)
        send_alert(error_msg, "CRITICAL", "Telegram Bot")


if __name__ == '__main__':
    main()
