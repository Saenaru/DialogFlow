from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv
from google.cloud import dialogflow
from google.oauth2 import service_account
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
DIALOGFLOW_KEY_FILE = "newagent-ucxn-8332c4ae589a.json"

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
        logger.error(f"Ошибка Dialogflow: {e}")
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
    logger.error(f"Ошибка: {context.error}")

def main():
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не найден в .env файле!")
        return
    
    if not DIALOGFLOW_PROJECT_ID:
        logger.error("❌ DIALOGFLOW_PROJECT_ID не найден в .env файле!")
        return
    
    if not os.path.exists(DIALOGFLOW_KEY_FILE):
        logger.error(f"❌ Файл {DIALOGFLOW_KEY_FILE} не найден!")
        return
    
    try:
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        dp.add_error_handler(error_handler)
        
        logger.info("🤖 Бот запускается...")
        updater.start_polling()
        logger.info("✅ Бот успешно запущен!")
        
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()