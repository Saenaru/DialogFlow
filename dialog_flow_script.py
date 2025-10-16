import requests
from google.cloud import dialogflow
from google.oauth2 import service_account
import os
from dotenv import load_dotenv


def download_json(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def create_intent(display_name, training_phrases, answer, dialogflow_key_file, dialogflow_project_id):
    credentials = service_account.Credentials.from_service_account_file(dialogflow_key_file)
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
    parent = f"projects/{dialogflow_project_id}/agent"
    response = intents_client.create_intent(
        request={
            "parent": parent,
            "intent": intent,
            "language_code": "ru"
        }
    )
    return response


def get_intents_data(json_url):
    data = download_json(json_url)
    return data


def import_intents_from_url(dialogflow_key_file, dialogflow_project_id, json_url):
    try:
        data = get_intents_data(json_url)
        created_count = 0
        errors = []
        for intent_name, intent_data in data.items():
            try:
                response = create_intent(
                    display_name=intent_name,
                    training_phrases=intent_data['questions'],
                    answer=intent_data['answer'],
                    dialogflow_key_file=dialogflow_key_file,
                    dialogflow_project_id=dialogflow_project_id
                )
                created_count += 1
            except Exception as e:
                errors.append(f"'{intent_name}': {e}")
                continue

        return {
            'success': True,
            'total_intents': len(data),
            'created_count': created_count,
            'errors': errors
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def show_import_results(results):
    if not results['success']:
        print(f"❌ Ошибка импорта: {results['error']}")
        return
    print(f"✅ JSON загружен. Найдено интентов: {results['total_intents']}")
    print(f"🔄 Создано новых интентов: {results['created_count']}")
    if results['errors']:
        print(f"\n⚠️  Произошло ошибок: {len(results['errors'])}")
        for error in results['errors']:
            print(f"   ❌ {error}")
    print("🎉 Импорт завершен!")
    print("\n⚠️  Не забудьте ОПУБЛИКОВАТЬ агента в Dialogflow Console!")


def main():
    load_dotenv()
    DIALOGFLOW_KEY_FILE = os.getenv("DIALOGFLOW_KEY_FILE")
    DIALOGFLOW_PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID")
    JSON_URL = os.getenv("JSON_URL")
    if not all([DIALOGFLOW_KEY_FILE, DIALOGFLOW_PROJECT_ID, JSON_URL]):
        print("❌ Ошибка: Не все необходимые переменные окружения установлены")
        return
    print("🤖 Импорт интентов в Dialogflow")
    print("=" * 50)
    print("📥 Скачиваем JSON файл...")
    results = import_intents_from_url(DIALOGFLOW_KEY_FILE, DIALOGFLOW_PROJECT_ID, JSON_URL)
    show_import_results(results)


if __name__ == '__main__':
    main()
