from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import os
import logging
import random
import time
from dialogflow_utils import setup_logging, send_alert, get_dialogflow_response, check_required_env_vars, validate_dialogflow_config

logger = logging.getLogger(__name__)


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
    response_text, is_fallback = get_dialogflow_response(text, str(user_id), platform='vk')
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
    setup_logging()

    logger.info("=== Запуск VK Bot ===")
    required_vars = ['VK_GROUP_TOKEN', 'VK_GROUP_ID', 'MONITORING_BOT_TOKEN', 'ADMIN_CHAT_ID']
    if not check_required_env_vars(required_vars, "VK Bot"):
        return
    if not validate_dialogflow_config("VK Bot"):
        return

    vk_api, longpoll = initialize_vk_bot()
    if vk_api and longpoll:
        run_bot_loop(vk_api, longpoll)


if __name__ == '__main__':
    main()
