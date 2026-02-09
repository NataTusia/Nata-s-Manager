import asyncio
import logging
import os
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- НАЛАШТУВАННЯ ---
# Токен беремо зі змінних середовища (безпечно)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Встав сюди свій числовий ID (щоб ніхто чужий не клацав твоїх ботів)
ALLOWED_USERS = [
    772888828,  # Це ти (Ната)
    433557714,  # Антон
    675199057,  # Елена
]

# ТВОЇ БОТИ (Назва кнопки -> Посилання на Render)
# Важливо: Посилання мають бути повними, з https://
MY_BOTS = {
    "🧸 KidsLand": "https://kidslend-ob1u.onrender.com",
    "🔮 Magic Bot": "https://magikindeteil-1cv2.onrender.com",
    "💸 Hesh & Cash": "https://haih-and-cash.onrender.com",
    "💻 Data Nata": "https://datanata-38o2.onrender.com"
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Клавіатура ---
def get_keyboard():
    builder = InlineKeyboardBuilder()
    # Створюємо кнопки динамічно зі словника
    for name in MY_BOTS.keys():
        # У callback_data передаємо частину назви
        safe_name = name.split(" ")[1] if " " in name else name # Беремо перше слово для ID
        builder.row(types.InlineKeyboardButton(text=f"🟢 Розбудити {name}", callback_data=f"wake_{safe_name}"))
    return builder.as_markup()

# --- Команда /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    # Перевіряємо, чи є людина у списку
    if user_id not in ALLOWED_USERS:
        # Пишемо чужинцю його ID, щоб він міг скинути його тобі для доступу
        await message.answer(f"⛔️ Доступ заборонено.\nТвій ID: {user_id}\nНадішли цей код адміністратору (Наті), щоб отримати доступ.")
        return
    
    await message.answer(
        "👋 <b>Вітаю, Директоре!</b>\n\n"
        "Усі системи в нормі. Роботяги сплять.\n"
        "Кого будемо будити для роботи?",
        reply_markup=get_keyboard(),
        parse_mode="HTML"
    )

# --- Обробка натискання кнопок ---
@dp.callback_query(F.data.startswith("wake_"))
async def wake_up_bot(callback: types.CallbackQuery):
    # Визначаємо, яку кнопку натиснули
    btn_code = callback.data.split("_")[1]
    
    target_url = None
    bot_name = ""

    # Шукаємо правильне посилання
    for name, url in MY_BOTS.items():
        if btn_code in name:
            target_url = url
            bot_name = name
            break
            
    if target_url:
        await callback.answer(f"⏳ Відправляю сигнал до {bot_name}...", show_alert=False)
        
        try:
            # "Стукаємо" по боту. Timeout маленький (2 сек), бо нам не треба чекати відповідь.
            # Головне - щоб сигнал пішов.
            requests.get(target_url, timeout=2)
        except Exception:
            # Якщо вилетіла помилка (наприклад, Timeout) - це нормально!
            # Render довго прокидається, тому ми не чекаємо повного завантаження тут.
            pass
            
        await callback.message.edit_text(
            f"🚀 <b>Сигнал успішно відправлено!</b>\n\n"
            f"🎯 Бот: <b>{bot_name}</b>\n"
            f"⏳ Він прокидається. Зачекай 10-30 секунд.\n"
            f"📩 Скоро він напише тобі в особисті.",
            reply_markup=get_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Помилка: Не знайдено посилання!", show_alert=True)

# --- Web Server (Щоб тримати Директора живим) ---
async def handle(request): return web.Response(text="Director Bot is Alive & Watching")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Запускаємо сервер
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Порт для Koyeb/Render
    port = int(os.environ.get("PORT", 8080)) 
    await web.TCPSite(runner, "0.0.0.0", port).start()
    
    # Запускаємо бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())