import os
import asyncio
import anthropic
from telethon import TelegramClient, events

# Налаштування
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

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
greeted_users = set()

client = TelegramClient('session', API_ID, API_HASH)


@client.on(events.NewMessage(incoming=True))
async def handle_message(event):
    if event.is_private:
        user_id = event.sender_id

        # Якщо фото
        if event.photo:
            await event.respond(
                "✅ Дякуємо! Скріншот отримано.\n\n"
                "Вашу заявку передано адміністратору на перевірку.\n"
                "Очікуйте підтвердження. Зазвичай це займає до 24 годин. ⏳"
            )
            return

        user_text = event.text
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

            await event.respond(reply)

        except Exception as e:
            print(f"Помилка Claude: {e}")


async def check_join_requests():
    print("Моніторинг заявок запущено...")
    processed = set()

    while True:
        try:
            from telethon.tl.functions.messages import GetChatInviteImportersRequest

            async for dialog in client.iter_dialogs():
                if dialog.is_channel:
                    try:
                        result = await client(GetChatInviteImportersRequest(
                            peer=dialog.entity,
                            link=None,
                            offset_date=None,
                            offset_user=None,
                            limit=100,
                            requested=True
                        ))

                        for importer in result.importers:
                            user_id = importer.user_id
                            if user_id not in processed and user_id not in greeted_users:
                                processed.add(user_id)
                                greeted_users.add(user_id)
                                conversation_history[user_id] = []

                                try:
                                    await client.send_message(user_id, WELCOME_MESSAGE)
                                    print(f"Надіслано привітання користувачу {user_id}")
                                except Exception as e:
                                    print(f"Не вдалось написати {user_id}: {e}")

                    except Exception:
                        pass

        except Exception as e:
            print(f"Помилка: {e}")

        await asyncio.sleep(30)


async def main():
    print("Userbot запускається...")
    await client.start()
    print("Userbot запущено!")

    await asyncio.gather(
        check_join_requests(),
        client.run_until_disconnected()
    )


if __name__ == "__main__":
    asyncio.run(main())
