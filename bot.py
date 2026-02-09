import asyncio
import logging
import os
import sys
from datetime import datetime
import pytz 
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web, ClientSession # <-- Асинхронний клієнт
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- НАЛАШТУВАННЯ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 772888828  # <--- ВСТАВ СВІЙ ID!
ALLOWED_USERS = [
    ADMIN_ID,    # Це ти (автоматично підтягнеться згори)
    433557714,  # <--- Заміни на ID першого друга (лиши коми в кінці)
    675199057,  # <--- Заміни на ID другого друга
]

# ТВОЇ БОТИ
MY_BOTS = {
    "🧸 KidsLand": "https://kidslend-ob1u.onrender.com",
    "🔮 Magic Bot": "https://magikindeteil-1cv2.onrender.com",
    "💸 Hesh & Cash": "https://haih-and-cash.onrender.com", 
    "💻 Data Nata": "https://datanata-38o2.onrender.com",
}

if not BOT_TOKEN:
    sys.exit("❌ Error: No Token")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
kyiv_tz = pytz.timezone('Europe/Kiev') # Фіксуємо Київський час

# --- КЛАВІАТУРА ---
def get_keyboard():
    builder = InlineKeyboardBuilder()
    for name in MY_BOTS.keys():
        safe_code = name.split(" ")[1] if " " in name else name
        builder.row(types.InlineKeyboardButton(text=f"🟢 Розбудити {name}", callback_data=f"wake_{safe_code}"))
    builder.row(types.InlineKeyboardButton(text=f"🚀 Розбудити ВСІХ", callback_data=f"wake_all"))
    builder.row(types.InlineKeyboardButton(text=f"🕒 Перевірити час", callback_data=f"check_time"))
    return builder.as_markup()

# --- ФУНКЦІЯ: АСИНХРОННИЙ "СТУК" ---
async def ping_url(url, session):
    try:
        async with session.get(url, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        print(f"⚠️ Помилка пінгу {url}: {e}")
        return False

# --- 1. ЗАГАЛЬНИЙ РАНКОВИЙ ОБХІД ---
async def morning_routine():
    print(f"⏰ ПОЧАТОК РАНКОВОГО ОБХОДУ: {datetime.now(kyiv_tz)}")
    try:
        await bot.send_message(ADMIN_ID, "☕️ <b>Доброго ранку!</b> Починаю будити команду...", parse_mode="HTML")
    except: pass

    results = []
    async with ClientSession() as session:
        for name, url in MY_BOTS.items():
            success = await ping_url(url, session)
            status = "✅ Прокинувся" if success else "⚠️ Не відповів"
            results.append(f"{name}: {status}")
            await asyncio.sleep(5) # Пауза між ботами
    
    report = "\n".join(results)
    try:
        await bot.send_message(ADMIN_ID, f"📋 <b>Звіт:</b>\n\n{report}", parse_mode="HTML")
    except: pass

# --- 2. СПЕЦІАЛЬНИЙ БУДИЛЬНИК (HESH) ---
async def wake_hesh_only():
    print(f"⏰ БУДИМО ХЕША: {datetime.now(kyiv_tz)}")
    url = MY_BOTS.get("💸 Hesh & Cash")
    if url:
        async with ClientSession() as session:
            await ping_url(url, session)
            try:
                await bot.send_message(ADMIN_ID, "💸 Hesh & Cash отримав сигнал!", parse_mode="HTML")
            except: pass

# --- ОБРОБКА КОМАНД ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id in ALLOWED_USERS:
        await message.answer(
            f"👋 Директор на посту.\nЧас сервера: {datetime.now(kyiv_tz).strftime('%H:%M')}", 
            reply_markup=get_keyboard()
        )

@dp.callback_query(F.data == "check_time")
async def check_time_btn(callback: types.CallbackQuery):
    now = datetime.now(kyiv_tz).strftime('%H:%M:%S')
    await callback.answer(f"Київський час: {now}", show_alert=True)

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
        async with ClientSession() as session:
            await ping_url(target_url, session)
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
    
    # ПЛАНУВАЛЬНИК
    scheduler.add_job(morning_routine, 'cron', hour=8, minute=55, timezone=kyiv_tz)
    scheduler.add_job(wake_hesh_only, 'cron', hour=13, minute=48, timezone=kyiv_tz)
    scheduler.add_job(wake_hesh_only, 'cron', hour=18, minute=55, timezone=kyiv_tz)
    
    scheduler.start()
    
    # Виводимо в лог час запуску
    print(f"✅ Бот запущено! Київський час: {datetime.now(kyiv_tz)}")
    print("⏰ Розклад:")
    print("- 08:55 (Всі)")
    print("- 13:48 (Хеш)")
    print("- 18:55 (Хеш)")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())