import os
import logging
import requests
from google.cloud import dialogflow
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )


def send_alert(message, level="INFO", bot_name="Bot"):
    MONITORING_BOT_TOKEN = os.getenv('MONITORING_BOT_TOKEN')
    ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
    
    if not MONITORING_BOT_TOKEN or not ADMIN_CHAT_ID:
        logger.warning("Monitoring bot token or admin chat ID not set")
        return

    try:
        formatted_message = f"{level} Alert - {bot_name}\n\n{message}"
        url = f"https://api.telegram.org/bot{MONITORING_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': ADMIN_CHAT_ID,
            'text': formatted_message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Alert sent to monitoring bot: {level}")

    except Exception as e:
        logger.error(f"Failed to send alert to monitoring bot: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response content: {e.response.text}")


def get_dialogflow_response(text, session_id, language_code='ru', platform='unknown'):
    DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
    DIALOGFLOW_KEY_FILE = os.getenv('DIALOGFLOW_KEY_FILE')
    
    try:
        platform_session_id = f"{platform}-{session_id}"
        logger.info(f"Dialogflow запрос для сессии: {platform_session_id}")
        
        credentials = service_account.Credentials.from_service_account_file(DIALOGFLOW_KEY_FILE)
        session_client = dialogflow.SessionsClient(credentials=credentials)
        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, platform_session_id)
        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        response = session_client.detect_intent(
            session=session,
            query_input=query_input
        )
        
        result = response.query_result
        is_fallback = result.intent.is_fallback
        logger.info(f"Dialogflow ответ: {result.fulfillment_text}")
        logger.info(f"Это fallback-интент: {is_fallback}")
        
        return result.fulfillment_text, is_fallback

    except Exception as e:
        error_msg = f"Ошибка Dialogflow: {e}"
        logger.error(error_msg)
        send_alert(error_msg, "ERROR", f"{platform.capitalize()} Bot")
        return "Извините, произошла ошибка при обработке запроса.", True


def check_required_env_vars(required_vars, bot_name):
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        error_msg = f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}"
        logger.error(error_msg)
        send_alert(error_msg, "CRITICAL", bot_name)
        return False
    
    return True


def validate_dialogflow_config(bot_name):
    DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
    DIALOGFLOW_KEY_FILE = os.getenv('DIALOGFLOW_KEY_FILE')
    
    if not DIALOGFLOW_PROJECT_ID:
        error_msg = "❌ DIALOGFLOW_PROJECT_ID не найден!"
        logger.error(error_msg)
        send_alert(error_msg, "CRITICAL", bot_name)
        return False
    
    if not os.path.exists(DIALOGFLOW_KEY_FILE):
        error_msg = f"❌ Файл {DIALOGFLOW_KEY_FILE} не найден!"
        logger.error(error_msg)
        send_alert(error_msg, "CRITICAL", bot_name)
        return False
    
    return True