import os
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# Ініціалізація Claude
claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Зберігаємо історію розмов для кожного користувача
conversation_history = {}

SYSTEM_PROMPT = """Ти корисний асистент у Telegram. Відповідай чітко, лаконічно та дружелюбно.
Якщо не знаєш відповіді — чесно скажи про це."""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text(
        "👋 Привіт! Я бот на базі Claude AI.\n"
        "Напиши мені будь-що — і я відповім!\n\n"
        "🔄 /reset — очистити історію розмови"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("✅ Історія розмови очищена. Починаємо заново!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # Ініціалізуємо історію якщо нова розмова
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # Додаємо повідомлення користувача в історію
    conversation_history[user_id].append({
        "role": "user",
        "content": user_text
    })

    # Обмежуємо історію до 20 повідомлень (10 туди/назад)
    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]

    # Показуємо що бот "друкує"
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        # Запит до Claude
        response = claude.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=conversation_history[user_id]
        )

        reply = response.content[0].text

        # Додаємо відповідь асистента в історію
        conversation_history[user_id].append({
            "role": "assistant",
            "content": reply
        })

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(
            "⚠️ Виникла помилка при зверненні до AI. Спробуй ще раз."
        )
        print(f"Помилка: {e}")


def main():
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущено!")
    app.run_polling()


if __name__ == "__main__":
    main()
