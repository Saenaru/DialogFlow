import requests
from google.cloud import dialogflow
from google.oauth2 import service_account

DIALOGFLOW_KEY_FILE = "newagent-ucxn-8332c4ae589a.json"
DIALOGFLOW_PROJECT_ID = "newagent-ucxn"

JSON_URL = "https://dvmn.org/media/filer_public/a7/db/a7db66c0-1259-4dac-9726-2d1fa9c44f20/questions.json"


def download_json(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def delete_existing_intents():
    print("🗑️ Удаляем существующие интенты...")
    credentials = service_account.Credentials.from_service_account_file(DIALOGFLOW_KEY_FILE)
    intents_client = dialogflow.IntentsClient(credentials=credentials)
    parent = f"projects/{DIALOGFLOW_PROJECT_ID}/agent"

    try:
        intents = intents_client.list_intents(parent=parent)
        for intent in intents:
            if intent.display_name != "Default Welcome Intent" and intent.display_name != "Default Fallback Intent":
                intents_client.delete_intent(name=intent.name)
                print(f"   Удален интент: {intent.display_name}")
    except Exception as e:
        print(f"❌ Ошибка при удалении интентов: {e}")


def create_intent(display_name, training_phrases, answer):
    credentials = service_account.Credentials.from_service_account_file(DIALOGFLOW_KEY_FILE)
    intents_client = dialogflow.IntentsClient(credentials=credentials)
    display_name = display_name.lower().replace(' ', '_')[:64]
    training_phrase_objects = []
    for phrase in training_phrases:
        part = dialogflow.Intent.TrainingPhrase.Part(text=phrase)
        training_phrase = dialogflow.Intent.TrainingPhrase(parts=[part])
        training_phrase_objects.append(training_phrase)
    text = dialogflow.Intent.Message.Text(text=[answer])
    message = dialogflow.Intent.Message(text=text)
    intent = dialogflow.Intent(
        display_name=display_name,
        training_phrases=training_phrase_objects,
        messages=[message]
    )
    parent = f"projects/{DIALOGFLOW_PROJECT_ID}/agent"
    response = intents_client.create_intent(
        request={
            "parent": parent,
            "intent": intent,
            "language_code": "ru"
        }
    )
    return response


def import_intents_from_url():
    print("📥 Скачиваем JSON файл...")
    try:
        data = download_json(JSON_URL)
        print(f"✅ JSON загружен. Найдено интентов: {len(data)}")
        delete_existing_intents()
        for intent_name, intent_data in data.items():
            print(f"🔄 Создаем интент: {intent_name}")
            try:
                response = create_intent(
                    display_name=intent_name,
                    training_phrases=intent_data['questions'],
                    answer=intent_data['answer']
                )
                print(f"✅ Интент '{intent_name}' создан успешно!")
                print(f"   📚 Training phrases: {len(intent_data['questions'])}")
                print(f"   💬 Ответ: {intent_data['answer'][:50]}...")
            except Exception as e:
                print(f"❌ Ошибка при создании интента '{intent_name}': {e}")
                continue
        print("🎉 Импорт завершен!")
        print("\n⚠️  Не забудьте ОПУБЛИКОВАТЬ агента в Dialogflow Console!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


def preview_intents():
    print("👀 Предпросмотр интентов:")

    try:
        data = download_json(JSON_URL)
        for intent_name, intent_data in data.items():
            print(f"\n📋 Интент: {intent_name}")
            print(f"   ❓ Вопросы: {len(intent_data['questions'])}")
            for i, question in enumerate(intent_data['questions'][:3]):
                print(f"      {i+1}. {question}")
            if len(intent_data['questions']) > 3:
                print(f"      ... и еще {len(intent_data['questions']) - 3} вопросов")
            print(f"   💬 Ответ: {intent_data['answer'][:100]}...")

        print(f"\n📊 Всего интентов: {len(data)}")
        print(f"📝 Всего вопросов: {sum(len(data[i]['questions']) for i in data)}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == '__main__':
    print("🤖 Импорт интентов в Dialogflow")
    print("=" * 50)
    preview_intents()
    print("\n" + "=" * 50)
    choice = input("\nХотите импортировать интенты? (y/n): ")
    if choice.lower() == 'y':
        print("\n🔄 Начинаем импорт...")
        print("⚠️  Это удалит существующие интенты и создаст новые на русском языке.")
        confirm = input("Продолжить? (y/n): ")
        if confirm.lower() == 'y':
            import_intents_from_url()
        else:
            print("👋 Импорт отменен")
    else:
        print("👋 Импорт отменен")
