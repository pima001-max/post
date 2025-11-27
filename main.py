import os
print("=== ДЕБАГ ТОКЕНА ===")
print("os.getenv('TOKEN')  →", repr(os.getenv("TOKEN")))
print("Длина токена       →", len(os.getenv("TOKEN") or ""))
print("os.environ.get('TOKEN') →", repr(os.environ.get("TOKEN")))
print("Все переменные окружения (первые 10):")
for i, key in enumerate(sorted(os.environ.keys())):
    if i >= 10: break
    value = os.environ[key]
    if "TOKEN" in key.upper():
        print(f"  {key} = {repr(value)}")
    else:
        print(f"  {key} = {repr(value[:30])}...")
print("======================")

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import json
from datetime import datetime

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHANNEL_ID = "@your_channel"

bot = Bot(TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
DB_FILE = "posts.json"

def load_posts():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_posts(posts):
    with open(DB_FILE, "w") as f:
        json.dump(posts, f, indent=4)

async def send_scheduled_posts():
    posts = load_posts()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    to_send = [p for p in posts if p["time"] == now]

    for post in to_send:
        if post["type"] == "text":
            await bot.send_message(CHANNEL_ID, post["content"])
        elif post["type"] == "audio":
            await bot.send_audio(CHANNEL_ID, FSInputFile(post["content"]))

    posts = [p for p in posts if p["time"] != now]
    save_posts(posts)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Бот работает. Отправь текст или .mp3 чтобы запланировать пост.")

@dp.message()
async def schedule(message: types.Message):
    posts = load_posts()

    if message.audio:
        file_id = message.audio.file_id
        file = await bot.get_file(file_id)
        path = f"files/{message.audio.file_unique_id}.mp3"
        await bot.download_file(file.file_path, path)
        await message.answer("Укажи дату и время (формат: 2025-12-31 18:30)")
        dp["pending"] = {"type": "audio", "content": path}
    else:
        dp["pending"] = {"type": "text", "content": message.text}
        await message.answer("Укажи дату и время (формат: 2025-12-31 18:30)")

@dp.message()
async def set_time(message: types.Message):
    if "pending" not in dp:
        return

    try:
        datetime.strptime(message.text, "%Y-%m-%d %H:%M")
    except:
        await message.answer("Неверный формат. Пример: 2025-12-31 18:30")
        return

    posts = load_posts()
    pending = dp["pending"]
    pending["time"] = message.text
    posts.append(pending)
    save_posts(posts)

    await message.answer("Пост запланирован!")
    dp["pending"] = None

async def main():
    scheduler.add_job(send_scheduled_posts, "interval", seconds=30)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
