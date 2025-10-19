import logging
import requests
from google.cloud import dialogflow
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def send_alert(message, level="INFO", bot_name="Bot", monitoring_config=None):
    if not monitoring_config:
        logger.warning("Monitoring configuration not provided")
        return

    try:
        formatted_message = f"{level} Alert - {bot_name}\n\n{message}"
        url = f"https://api.telegram.org/bot{monitoring_config['token']}/sendMessage"
        payload = {
            'chat_id': monitoring_config['admin_chat_id'],
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


def get_dialogflow_response(text, session_id, dialogflow_config, language_code='ru', platform='unknown'):
    if not dialogflow_config:
        error_msg = "Dialogflow configuration not provided"
        logger.error(error_msg)
        return "Извините, произошла ошибка при обработке запроса.", True

    try:
        platform_session_id = f"{platform}-{session_id}"
        logger.info(f"Dialogflow запрос для сессии: {platform_session_id}")
        credentials = service_account.Credentials.from_service_account_file(dialogflow_config['key_file'])
        session_client = dialogflow.SessionsClient(credentials=credentials)
        session = session_client.session_path(dialogflow_config['project_id'], platform_session_id)
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
        return "Извините, произошла ошибка при обработке запроса.", True
