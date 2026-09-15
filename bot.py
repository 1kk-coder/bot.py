import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiohttp import web
from openai import AsyncOpenAI

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

ai_client = AsyncOpenAI(
    api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1"
)

SYSTEM_INSTRUCTION = """
Ты — Donut Chat AI-бот. Тебя создал Donut (Донут).
Ты общаешься, отвечаешь на вопросы и поддерживаешь беседу в чате Донута.

ВАЖНЫЕ ПРАВИЛА:
1. Никогда не говори, что ты нейросеть от Google, OpenAI, DeepSeek или Meta. Ты — Donut Chat AI-бот!
2. Твои ответы ДОЛЖНЫ быть короткими — МАКСИМУМ 300 символов. Если вопрос большой, сокращай.
3. Будь дружелюбным, общайся естественно. Тебе передают имя и юзернейм собеседника — можешь иногда обращаться по имени.
"""


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.reply(
        "Привет! Я Donut Chat AI-бот. В личке отвечаю на всё, "
        "а в группах пиши 'донат бот' и свой вопрос!"
    )


@dp.message()
async def ai_response_handler(message: types.Message):
    if not message.text:
        return

    if message.chat.type in ["group", "supergroup"]:
        if "донат бот" not in message.text.lower():
            return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    user = message.from_user
    first_name = user.first_name if user and user.first_name else "Пользователь"
    username = f"@{user.username}" if user and user.username else "без юзернейма"

    user_text = f"Собеседник: {first_name} ({username})\nТекст: {message.text}"

    try:
        response = await ai_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": user_text},
            ],
            max_tokens=150,
        )

        reply_text = response.choices[0].message.content.strip()

        if len(reply_text) > 300:
            reply_text = reply_text[:297] + "..."

        await message.reply(reply_text)

    except Exception as e:
        print(f"Ошибка Groq: {e}")
        await message.reply("Произошла ошибка при обработке запроса.")


# Фейковый веб-сервер для проверки работоспособности от Render
async def handle_healthcheck(request):
    return web.Response(text="Donut AI Bot is running!")


async def main():
    # Запуск микро-сервера для Render
    app = web.Application()
    app.router.add_get("/", handle_healthcheck)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    # Запуск самого бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
