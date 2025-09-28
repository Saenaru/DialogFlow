from vk_api import VkApi
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from google.cloud import dialogflow
from google.oauth2 import service_account
from dotenv import load_dotenv
import os
import logging
import random
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('vk_bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


load_dotenv()

VK_GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN')
VK_GROUP_ID = os.getenv('VK_GROUP_ID')
DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
DIALOGFLOW_KEY_FILE = "newagent-ucxn-8332c4ae589a.json"

def get_dialogflow_response(text, session_id, language_code='ru'):
    try:
        logger.info(f"Dialogflow запрос: {text} для сессии {session_id}")
        
        credentials = service_account.Credentials.from_service_account_file(DIALOGFLOW_KEY_FILE)
        session_client = dialogflow.SessionsClient(credentials=credentials)
        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)
        
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
        logger.error(f"Ошибка Dialogflow: {e}")
        return "Извините, произошла ошибка при обработке запроса.", True

class VKBot:
    def __init__(self, group_token, group_id):
        try:
            logger.info("Инициализация VK бота...")
            self.vk_session = VkApi(token=group_token)
            self.vk = self.vk_session.get_api()
            self.longpoll = VkBotLongPoll(self.vk_session, group_id)
            logger.info("VK бот инициализирован успешно")
        except Exception as e:
            logger.error(f"Ошибка инициализации VK бота: {e}")
            raise
    
    def send_message(self, user_id, message):
        try:
            self.vk.messages.send(
                user_id=user_id,
                message=message,
                random_id=random.randint(1, 10000)
            )
            logger.info(f"Сообщение отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
    
    def handle_start(self, user_id):
        welcome_message = (
            "Привет! Я умный бот с интеграцией Dialogflow. "
            "Задайте мне любой вопрос! Если я не смогу помочь, "
            "вам ответит оператор техподдержки."
        )
        self.send_message(user_id, welcome_message)
    
    def handle_message(self, user_id, text):
        response_text, is_fallback = get_dialogflow_response(text, str(user_id))
        
        if is_fallback:
            logger.info(f"Fallback-интент обнаружен для пользователя {user_id}. Сообщение не отправляется.")
            return
        
        self.send_message(user_id, response_text)
    
    def run(self):
        logger.info("🤖 VK Бот запускается...")
        
        while True:
            try:
                logger.info("Ожидание событий LongPoll...")
                for event in self.longpoll.listen():
                    if event.type == VkBotEventType.MESSAGE_NEW:
                        message = event.object.message
                        user_id = message['from_id']
                        text = message['text'].strip()
                        
                        logger.info(f"Получено сообщение от {user_id}: {text}")
                        
                        if text.lower() in ['/start', 'start', 'начать', 'старт', 'привет']:
                            self.handle_start(user_id)
                        else:
                            self.handle_message(user_id, text)
                            
            except Exception as e:
                logger.error(f"Ошибка в основном цикле: {e}")
                logger.info("Перезапуск через 10 секунд...")
                time.sleep(10)

def check_environment():
    errors = []
    
    if not VK_GROUP_TOKEN:
        errors.append("❌ VK_GROUP_TOKEN не найден в переменных окружения!")
    
    if not VK_GROUP_ID:
        errors.append("❌ VK_GROUP_ID не найден в переменных окружения!")
    
    if not DIALOGFLOW_PROJECT_ID:
        errors.append("❌ DIALOGFLOW_PROJECT_ID не найден в переменных окружения!")
    
    if not os.path.exists(DIALOGFLOW_KEY_FILE):
        errors.append(f"❌ Файл {DIALOGFLOW_KEY_FILE} не найден!")
    
    if VK_GROUP_ID and not VK_GROUP_ID.isdigit():
        errors.append("❌ VK_GROUP_ID должен содержать только цифры!")
    
    return errors

def main():
    logger.info("=== Запуск проверки окружения ===")
    
    errors = check_environment()
    if errors:
        for error in errors:
            logger.error(error)
        return
    
    logger.info("✅ Все переменные окружения проверены успешно")
    
    logger.info(f"VK_GROUP_ID: {VK_GROUP_ID}")
    logger.info(f"DIALOGFLOW_PROJECT_ID: {DIALOGFLOW_PROJECT_ID}")
    logger.info(f"DIALOGFLOW_KEY_FILE существует: {os.path.exists(DIALOGFLOW_KEY_FILE)}")
    
    try:
        bot = VKBot(VK_GROUP_TOKEN, VK_GROUP_ID)
        logger.info("✅ Бот успешно инициализирован, запуск основного цикла...")
        bot.run()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()