from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv
import logging
import os

load_dotenv()


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

def start(update, context):
    update.message.reply_text("Привет! Я бот-повторюшка!")

def echo(update, context):
    update.message.reply_text(update.message.text)

def main():
    TOKEN = os.getenv('BOT_TOKEN')
    
    if not TOKEN:
        print("❌ Ошибка: Токен не найден в .env файле!")
        return
        
    try:
        updater = Updater(TOKEN, use_context=True)
        
        dp = updater.dispatcher
        
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
        
        print("Бот запускается...")
        updater.start_polling()
        print("Бот успешно запущен!")
        
        updater.idle()
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    main()