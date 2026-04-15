import os
import asyncio
import anthropic
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ChatJoinRequestHandler, filters, ContextTypes

# Налаштування
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ADMIN_TELEGRAM_ID = int(os.environ.get("ADMIN_TELEGRAM_ID", "0"))

LINK_NEW = "https://gguapromo.com/l/694bf8aa934079ff9d09ee13"
LINK_HAS_ACCOUNT_1 = "https://click.cpahome-track.com/sK2ffaE0"
LINK_HAS_ACCOUNT_2 = "https://click.trafficeratrack.com/U7PXF5Wh"

WELCOME_MESSAGE = """👋 Вітаємо! Дякуємо за інтерес до нашої команди!

Якщо ви хочете почати співпрацю, будь ласка, уважно ознайомтесь із наступними умовами:

⬇️ Для того щоб приєднатися до команди, потрібно виконати всі кроки, зазначені нижче.

❗️УВАЖНІСТЬ ТА ВИКОНАННЯ ВСІХ ВИМОГ — запорука успішної співпраці!

1️⃣ Реєстрацію необхідно пройти виключно за цим посиланням:

😎 https://gguapromo.com/l/694bf8aa934079ff9d09ee13 😎

Потрібно повністю завершити процес реєстрації: створити логін і пароль, а також пройти верифікацію.
(Через застосунок ДІЯ це займе лише близько 1 хвилини.)

2️⃣ Після того як реєстрація буде завершена, надішліть, будь ласка, скріншот вашого акаунта в особисті повідомлення.

Якщо у вас вже є зареєстрований акаунт — обов'язково повідомте нам про це! ✅"""

SYSTEM_PROMPT = """Ти менеджер по набору команди. Твоя задача — ввічливо та переконливо довести людину до реєстрації та надсилання скріншоту акаунта.

Контекст:
- Посилання для нових: https://gguapromo.com/l/694bf8aa934079ff9d09ee13
- Посилання якщо є акаунт на першій платформі: https://click.cpahome-track.com/sK2ffaE0
- Посилання якщо є акаунт на другій платформі: https://click.trafficeratrack.com/U7PXF5Wh

Правила:
- Спілкуйся виключно українською мовою
- Будь дружелюбним але наполегливим
- Якщо людина каже що вже є акаунт — запитай на якій платформі і дай відповідне посилання
- Якщо людина каже що зареєструвалась — проси скріншот акаунта
- Якщо людина надіслала фото — подякуй і скажи що передаєш адміністратору на перевірку
- Якщо людина вагається — мотивуй і переконуй
- Відповідай коротко і чітко"""

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
conversation_history = {}


async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Спрацьовує коли хтось подає заявку на вступ в канал"""
    user = update.chat_join_request.from_user
    user_id = user.id
    chat_id = update.chat_join_request.chat.id

    print(f"Нова заявка від {user.first_name} (@{user.username}, ID: {user_id})")

    # Ініціалізуємо історію розмови
    conversation_history[user_id] = []

    try:
        # Надсилаємо привітальне повідомлення в особисті
        await context.bot.send_message(
            chat_id=user_id,
            text=WELCOME_MESSAGE
        )
        print(f"Привітання надіслано {user_id}")

        # Сповіщаємо адміна
        if ADMIN_TELEGRAM_ID:
            await context.bot.send_message(
                chat_id=ADMIN_TELEGRAM_ID,
                text=f"📥 Нова заявка на вступ!\n\n"
                     f"👤 Ім'я: {user.first_name} {user.last_name or ''}\n"
                     f"🔗 Username: @{user.username or 'немає'}\n"
                     f"🆔 ID: {user_id}"
            )
    except Exception as e:
        print(f"Не вдалось написати користувачу {user_id}: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє повідомлення від користувачів"""
    user_id = update.effective_user.id

    # Якщо фото
    if update.message.photo:
        await update.message.reply_text(
            "✅ Дякуємо! Скріншот отримано.\n\n"
            "Вашу заявку передано адміністратору на перевірку.\n"
            "Очікуйте підтвердження. Зазвичай це займає до 24 годин. ⏳"
        )
        # Сповіщаємо адміна
        if ADMIN_TELEGRAM_ID:
            user = update.effective_user
            await context.bot.send_message(
                chat_id=ADMIN_TELEGRAM_ID,
                text=f"📸 Скріншот від:\n"
                     f"👤 {user.first_name} @{user.username or 'немає'}\n"
                     f"🆔 ID: {user_id}"
            )
            await context.bot.forward_message(
                chat_id=ADMIN_TELEGRAM_ID,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id
            )
        return

    user_text = update.message.text
    if not user_text:
        return

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": user_text
    })

    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = claude.messages.create(
            model="claude-opus-4-5",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=conversation_history[user_id]
        )
        reply = response.content[0].text

        conversation_history[user_id].append({
            "role": "assistant",
            "content": reply
        })

        await update.message.reply_text(reply)

    except Exception as e:
        print(f"Помилка Claude: {e}")
        await update.message.reply_text("⚠️ Виникла помилка. Спробуйте ще раз.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text(WELCOME_MESSAGE)


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущено! Очікуємо заявки...")
    app.run_polling(allowed_updates=["message", "chat_join_request"])


if __name__ == "__main__":
    main()
