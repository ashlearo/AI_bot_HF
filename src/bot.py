import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient

# Конфигурация через переменные окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
MODEL_NAME = "mistralai/Mixtral-8x7B-Instruct-v0.1"  # Или другая модель

# Инициализация клиента Hugging Face
client = InferenceClient(api_key=HF_API_KEY)

# Хранилище истории диалогов
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Задай мне вопрос, и я постараюсь ответить.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    user_input = update.message.text

    # Инициализация сессии для нового пользователя
    if user_id not in user_sessions:
        user_sessions[user_id] = []

    # Добавляем новый вопрос в историю
    user_sessions[user_id].append({"role": "user", "content": user_input})

    try:
        # Формируем промпт с историей диалога
        messages = [
            {"role": "system", "content": "Ты полезный ассистент. Отвечай кратко и точно."},
            *user_sessions[user_id][-3:]  # Берём последние 3 сообщения для контекста
        ]

        # Отправляем запрос к модели
        response = client.chat_completion(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=500,
            stream=True  # Для постепенного получения ответа
        )

        # Постепенно отправляем ответ пользователю
        full_response = []
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                full_response.append(chunk.choices[0].delta.content)
                if len(full_response) % 50 == 0:  # Отправляем частями
                    await update.message.reply_text(''.join(full_response[-50:]))
        
        # Сохраняем полный ответ в историю
        user_sessions[user_id].append({"role": "assistant", "content": ''.join(full_response)})

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")
        del user_sessions[user_id]  # Сбрасываем сессию при ошибке

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
