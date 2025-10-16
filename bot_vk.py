from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from google.cloud import dialogflow
from google.oauth2 import service_account
from dotenv import load_dotenv
import os
import logging
import random
import time
import requests

logger = logging.getLogger(__name__)


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )


def send_alert(message, level="INFO", bot_name="VK Bot"):
    MONITORING_BOT_TOKEN = os.getenv('MONITORING_BOT_TOKEN')
    ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
    
    if not MONITORING_BOT_TOKEN or not ADMIN_CHAT_ID:
        return
    try:
        formatted_message = f"🔔 *{level} - {bot_name}*\n\n{message}"
        url = f"https://api.telegram.org/bot{MONITORING_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': ADMIN_CHAT_ID,
            'text': formatted_message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Alert отправлен: {level}")
    except Exception as e:
        logger.error(f"Ошибка отправки alert: {e}")


def get_dialogflow_response(text, session_id, language_code='ru'):
    DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
    DIALOGFLOW_KEY_FILE = os.getenv('DIALOGFLOW_KEY_FILE')
    try:
        platform_session_id = f"vk-{session_id}"
        logger.info(f"Dialogflow запрос: {text} для сессии {platform_session_id}")
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
        send_alert(error_msg, "ERROR", "VK Bot")
        return "Извините, произошла ошибка при обработке запроса.", True


def send_message(vk_api, user_id, message):
    try:
        vk_api.messages.send(
            user_id=user_id,
            message=message,
            random_id=random.randint(1, 10000)
        )
        logger.info(f"Сообщение отправлено пользователю {user_id}")
    except Exception as e:
        error_msg = f"Ошибка отправки сообщения пользователю {user_id}: {e}"
        logger.error(error_msg)
        send_alert(error_msg, "ERROR", "VK Bot")


def handle_start(vk_api, user_id):
    welcome_message = (
        "Привет!"
        "Задайте мне любой вопрос! Если я не смогу помочь, "
        "вам ответит оператор техподдержки."
    )
    send_message(vk_api, user_id, welcome_message)


def handle_user_message(vk_api, user_id, text):
    response_text, is_fallback = get_dialogflow_response(text, str(user_id))
    if is_fallback:
        logger.info(f"Fallback-интент обнаружен для пользователя {user_id}. Сообщение не отправляется.")
        return
    send_message(vk_api, user_id, response_text)


def initialize_vk_bot():
    VK_GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN')
    VK_GROUP_ID = os.getenv('VK_GROUP_ID')
    
    logger.info("🤖 VK Бот запускается...")
    try:
        logger.info("Инициализация VK бота...")
        vk_session = VkApi(token=VK_GROUP_TOKEN)
        vk_api = vk_session.get_api()
        longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID)
        group_info = vk_api.groups.getById(group_id=VK_GROUP_ID)
        group_name = group_info[0]['name'] if group_info else 'Unknown'
        logger.info(f"VK бот инициализирован для группы: {group_name}")
        send_alert(
            f"✅ VK Bot успешно запущен!\n"
            f"👥 Группа: {group_name}\n"
            f"🆔 ID: {VK_GROUP_ID}\n"
            f"📊 Статус: Активен и слушает события",
            "INFO",
            "VK Bot"
        )
        logger.info("✅ VK Bot успешно запущен и готов к работе!")
        return vk_api, longpoll
    except Exception as e:
        error_msg = f"Ошибка инициализации VK бота: {e}"
        logger.error(error_msg)
        send_alert(error_msg, "ERROR", "VK Bot")
        return None, None


def run_bot_loop(vk_api, longpoll):
    while True:
        try:
            logger.info("Ожидание событий LongPoll...")
            for event in longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    message = event.object.message
                    user_id = message['from_id']
                    text = message['text'].strip()
                    logger.info(f"Получено сообщение от {user_id}: {text}")
                    if text.lower() in ['/start', 'start', 'начать', 'старт', 'привет']:
                        handle_start(vk_api, user_id)
                    else:
                        handle_user_message(vk_api, user_id, text)

        except Exception as e:
            error_msg = f"Ошибка в основном цикле VK Bot: {e}"
            logger.error(error_msg)
            send_alert(error_msg, "ERROR", "VK Bot")
            logger.info("Перезапуск через 10 секунд...")
            time.sleep(10)


def main():
    load_dotenv()
    setup_logging()

    logger.info("=== Запуск VK Bot ===")

    VK_GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN')
    VK_GROUP_ID = os.getenv('VK_GROUP_ID')
    DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
    DIALOGFLOW_KEY_FILE = os.getenv('DIALOGFLOW_KEY_FILE')

    if not VK_GROUP_TOKEN:
        error_msg = "❌ VK_GROUP_TOKEN не найден!"
        logger.error(error_msg)
        send_alert(error_msg, "ERROR", "VK Bot")
        return

    if not VK_GROUP_ID:
        error_msg = "❌ VK_GROUP_ID не найден!"
        logger.error(error_msg)
        send_alert(error_msg, "ERROR", "VK Bot")
        return

    if not DIALOGFLOW_PROJECT_ID:
        error_msg = "❌ DIALOGFLOW_PROJECT_ID не найден!"
        logger.error(error_msg)
        send_alert(error_msg, "ERROR", "VK Bot")
        return

    if not os.path.exists(DIALOGFLOW_KEY_FILE):
        error_msg = f"❌ Файл {DIALOGFLOW_KEY_FILE} не найден!"
        logger.error(error_msg)
        send_alert(error_msg, "ERROR", "VK Bot")
        return

    vk_api, longpoll = initialize_vk_bot()
    if vk_api and longpoll:
        run_bot_loop(vk_api, longpoll)


if __name__ == '__main__':
    main()