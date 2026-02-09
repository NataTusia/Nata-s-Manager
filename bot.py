import asyncio
import logging
import os
import sys
import requests
from datetime import datetime
import pytz # Для часових поясів
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- НАЛАШТУВАННЯ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 123456789  # <--- ТВІЙ ID (Залиш той, що був)
ALLOWED_USERS = [ADMIN_ID]

# ТВОЇ БОТИ
MY_BOTS = {
    "🧸 KidsLand": "https://kidsland-xxxx.onrender.com",
    "🔮 Magic Bot": "https://magic-xxxx.onrender.com",
    "💸 Hesh & Cash": "https://hesh-xxxx.onrender.com", # Перевір, щоб тут було правильне посилання!
    "💻 Data Nata": "https://data-nata-xxxx.onrender.com",
}

if not BOT_TOKEN:
    sys.exit("❌ Error: No Token")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# --- КЛАВІАТУРА ---
def get_keyboard():
    builder = InlineKeyboardBuilder()
    for name in MY_BOTS.keys():
        safe_code = name.split(" ")[1] if " " in name else name
        builder.row(types.InlineKeyboardButton(text=f"🟢 Розбудити {name}", callback_data=f"wake_{safe_code}"))
    builder.row(types.InlineKeyboardButton(text=f"🚀 Розбудити ВСІХ", callback_data=f"wake_all"))
    return builder.as_markup()

# --- 1. ЗАГАЛЬНИЙ РАНКОВИЙ ОБХІД (ВСІХ) ---
async def morning_routine():
    try:
        await bot.send_message(ADMIN_ID, "☕️ <b>Доброго ранку!</b> Починаю будити команду...", parse_mode="HTML")
    except: pass

    results = []
    for name, url in MY_BOTS.items():
        try:
            requests.get(url, timeout=2)
            results.append(f"✅ {name}")
        except:
            results.append(f"⚠️ {name} (помилка)")
        await asyncio.sleep(5) # Пауза, щоб не перевантажити сервер
    
    try:
        await bot.send_message(ADMIN_ID, f"📋 <b>Ранковий звіт:</b>\n\n" + "\n".join(results), parse_mode="HTML")
    except: pass

# --- 2. СПЕЦІАЛЬНИЙ БУДИЛЬНИК ДЛЯ HESH & CASH ---
async def wake_hesh_only():
    # Шукаємо посилання саме на Хеша
    hesh_url = MY_BOTS.get("💸 Hesh & Cash")
    
    if hesh_url:
        try:
            requests.get(hesh_url, timeout=5)
            await bot.send_message(ADMIN_ID, "💸 <b>Hesh & Cash</b> розбуджений для додаткової роботи!", parse_mode="HTML")
        except Exception as e:
            print(f"Не вдалося розбудити Хеша: {e}")

# --- ОБРОБКА КОМАНД ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id in ALLOWED_USERS:
        await message.answer("👋 Директор на посту.\n\n⏰ <b>Розклад:</b>\n08:55 - Всі боти\n13:48 - Hesh & Cash\n18:55 - Hesh & Cash", reply_markup=get_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "wake_all")
async def manual_wake_all(callback: types.CallbackQuery):
    await callback.answer("Запускаю всіх...")
    await morning_routine()

@dp.callback_query(F.data.startswith("wake_"))
async def wake_single(callback: types.CallbackQuery):
    code = callback.data.split("_")[1]
    target_url = None
    for name, url in MY_BOTS.items():
        if code in name:
            target_url = url
            break
    if target_url:
        requests.get(target_url, timeout=2)
        await callback.answer(f"Сигнал надіслано!", show_alert=False)

# --- WEB SERVER ---
async def handle(request): return web.Response(text="Manager is Awake")
async def start_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, "0.0.0.0", port).start()

# --- ГОЛОВНА ФУНКЦІЯ ---
async def main():
    logging.basicConfig(level=logging.INFO)
    await start_server()
    
    # НАЛАШТУВАННЯ ЧАСУ
    kyiv_tz = pytz.timezone('Europe/Kiev')
    
    # 1. Ранок (Всі боти) - 08:55
    scheduler.add_job(morning_routine, 'cron', hour=8, minute=55, timezone=kyiv_tz)
    
    # 2. Обід (Тільки Hesh) - 13:48
    scheduler.add_job(wake_hesh_only, 'cron', hour=14, minute=40, timezone=kyiv_tz)

    # 3. Вечір (Тільки Hesh) - 18:55
    scheduler.add_job(wake_hesh_only, 'cron', hour=18, minute=55, timezone=kyiv_tz)
    
    scheduler.start()
    print("⏰ Всі будильники налаштовано!")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())