from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import os
import logging
import random
import time
from dialogflow_utils import setup_logging, send_alert, get_dialogflow_response
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def send_message(vk_api, user_id, message, monitoring_config):
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
        send_alert(error_msg, "ERROR", "VK Bot", monitoring_config)


def handle_start(vk_api, user_id, monitoring_config):
    welcome_message = (
        "Привет!"
        "Задайте мне любой вопрос! Если я не смогу помочь, "
        "вам ответит оператор техподдержки."
    )
    send_message(vk_api, user_id, welcome_message, monitoring_config)


def handle_user_message(vk_api, user_id, text, dialogflow_config, monitoring_config):
    session_id = f"vk-{user_id}"
    response_text, is_fallback = get_dialogflow_response(
        text, 
        session_id,
        dialogflow_config,
        platform='vk'
    )
    if is_fallback:
        logger.info(f"Fallback-интент обнаружен для пользователя {user_id}. Сообщение не отправляется.")
        return
    send_message(vk_api, user_id, response_text, monitoring_config)


def initialize_vk_bot(vk_group_token, vk_group_id, dialogflow_config, monitoring_config):
    logger.info("🤖 VK Бот запускается...")
    try:
        logger.info("Инициализация VK бота...")
        vk_session = VkApi(token=vk_group_token)
        vk_api = vk_session.get_api()
        longpoll = VkBotLongPoll(vk_session, vk_group_id)
        group_info = vk_api.groups.getById(group_id=vk_group_id)
        group_name = group_info[0]['name'] if group_info else 'Unknown'
        logger.info(f"VK бот инициализирован для группы: {group_name}")
        send_alert(
            f"✅ VK Bot успешно запущен!\n"
            f"👥 Группа: {group_name}\n"
            f"🆔 ID: {vk_group_id}\n"
            f"📊 Статус: Активен и слушает события",
            "INFO",
            "VK Bot",
            monitoring_config
        )
        logger.info("✅ VK Bot успешно запущен и готов к работе!")
        return vk_api, longpoll
    except Exception as e:
        error_msg = f"Ошибка инициализации VK бота: {e}"
        logger.error(error_msg)
        send_alert(error_msg, "ERROR", "VK Bot", monitoring_config)
        return None, None


def run_bot_loop(vk_api, longpoll, dialogflow_config, monitoring_config):
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
                        handle_start(vk_api, user_id, monitoring_config)
                    else:
                        handle_user_message(vk_api, user_id, text, dialogflow_config, monitoring_config)

        except Exception as e:
            error_msg = f"Ошибка в основном цикле VK Bot: {e}"
            logger.error(error_msg)
            send_alert(error_msg, "ERROR", "VK Bot", monitoring_config)
            logger.info("Перезапуск через 10 секунд...")
            time.sleep(10)


def main():
    load_dotenv()
    setup_logging()
    logger.info("=== Запуск VK Bot ===")
    vk_group_token = os.getenv('VK_GROUP_TOKEN')
    vk_group_id = os.getenv('VK_GROUP_ID')
    monitoring_token = os.getenv('MONITORING_BOT_TOKEN')
    admin_chat_id = os.getenv('ADMIN_CHAT_ID')
    dialogflow_project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
    dialogflow_key_file = os.getenv('DIALOGFLOW_KEY_FILE')

    if not all([vk_group_token, vk_group_id, monitoring_token, admin_chat_id, dialogflow_project_id, dialogflow_key_file]):
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

    vk_api, longpoll = initialize_vk_bot(vk_group_token, vk_group_id, dialogflow_config, monitoring_config)
    if vk_api and longpoll:
        run_bot_loop(vk_api, longpoll, dialogflow_config, monitoring_config)


if __name__ == '__main__':
    main()