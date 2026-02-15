import os
import asyncio
import logging

from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN, ADMIN_ID, BOT_USERNAME
from database import *

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ====== WEBHOOK НАСТРОЙКИ ======
WEBHOOK_PATH = "/webhook"
APP_URL = os.getenv("APP_URL", "").rstrip("/")
WEBHOOK_URL = f"{APP_URL}{WEBHOOK_PATH}" if APP_URL else ""

# ====== СОСТОЯНИЯ ======
class AddProduct(StatesGroup):
    currency = State()
    amount = State()
    price = State()

# ====== КЛАВИАТУРЫ ======
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 Купить монеты", callback_data="coins")],
        [InlineKeyboardButton(text="💵 Купить баксы", callback_data="bucks")],
        [InlineKeyboardButton(text="🤝 Партнёрская программа", callback_data="ref")]
    ])

def back_to_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_product")],
        [InlineKeyboardButton(text="❌ Удалить товар", callback_data="delete_product")],
        [InlineKeyboardButton(text="📋 Заказы", callback_data="orders")],
        [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back")]
    ])

def back_to_admin():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin_back")]
    ])

# ====== START ======
@dp.message(F.text.startswith("/start"))
async def start(message: Message):
    args = message.text.split()
    ref = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    if ref == message.from_user.id:
        ref = None

    add_user(message.from_user.id, ref)

    text = """
╔══════════════════════╗
   🏁 DRAG RACING SHOP 🏁
╚══════════════════════╝

💎 Самые низкие цены  
⚡ Быстрое выполнение  
🔐 100% безопасно  
👥 Много довольных клиентов  
🛡 Надёжно и проверено  

━━━━━━━━━━━━━━━━━━
Выберите раздел 👇
"""
    await message.answer(text, reply_markup=main_menu())

# ====== ПОКУПКА COINS ======
@dp.callback_query(F.data == "coins")
async def coins(callback: CallbackQuery):
    products = get_products("coins")
    buttons = []

    for p in products:
        buttons.append([InlineKeyboardButton(
            text=f"🪙 {p[2]} ┃ 💰 {p[3]}₽",
            callback_data=f"buy_{p[0]}"
        )])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])

    await callback.message.edit_text(
        "🪙 Выберите тариф:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# ====== ПОКУПКА BUCKS ======
@dp.callback_query(F.data == "bucks")
async def bucks(callback: CallbackQuery):
    products = get_products("bucks")
    buttons = []

    for p in products:
        buttons.append([InlineKeyboardButton(
            text=f"💵 {p[2]} ┃ 💰 {p[3]}₽",
            callback_data=f"buy_{p[0]}"
        )])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])

    await callback.message.edit_text(
        "💵 Выберите тариф:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# ====== ВЫБОР ТОВАРА ======
@dp.callback_query(F.data.startswith("buy_"))
async def buy(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    p = get_product(product_id)

    order_id = create_order(callback.from_user.id, p[3], product_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплата по СБП", callback_data=f"pay_{order_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])

    await callback.message.edit_text(
        f"📦 {p[2]}\n💰 К оплате: {p[3]}₽",
        reply_markup=keyboard
    )

# ====== ОПЛАТА ======
@dp.callback_query(F.data.startswith("pay_"))
async def pay(callback: CallbackQuery):
    qr = FSInputFile("qr.jpg")

    await callback.message.answer_photo(
        qr,
        caption="💳 Оплатите выбранную сумму и пришлите чек 💸\n\n🌐 Перед оплатой выключите VPN ✅"
    )

# ====== ОБРАБОТКА ЧЕКА ======
@dp.message(F.photo)
async def check_handler(message: Message):
    await message.answer("✅ Заявка подана, ожидайте подтверждения")

    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"📥 Новый чек от {message.from_user.id}"
    )

# ====== РЕФЕРАЛКА ======
@dp.callback_query(F.data == "ref")
async def referral(callback: CallbackQuery):
    link = f"https://t.me/{BOT_USERNAME}?start={callback.from_user.id}"

    text = f"""
🤝 ПАРТНЁРСКАЯ ПРОГРАММА

💸 Получайте 25% с каждой покупки друга
🔥 Без ограничений

Ваша ссылка:
{link}
"""
    await callback.message.edit_text(text, reply_markup=back_to_main())

# ====== НАЗАД В ГЛАВНОЕ ======
@dp.callback_query(F.data == "back")
async def go_back(callback: CallbackQuery):
    await callback.message.edit_text("Главное меню 👇", reply_markup=main_menu())

# ====== АДМИН ПАНЕЛЬ ======
@dp.message(F.text == "/admin")
async def admin(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Админ панель:", reply_markup=admin_menu())

@dp.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("👑 Админ панель:", reply_markup=admin_menu())

# ====== ДОБАВЛЕНИЕ ТОВАРА ======
@dp.callback_query(F.data == "add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.set_state(AddProduct.currency)
    await callback.message.answer("Введите тип: coins или bucks", reply_markup=back_to_admin())

@dp.message(AddProduct.currency)
async def set_currency(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    currency = message.text.strip().lower()
    if currency not in ("coins", "bucks"):
        await message.answer("❌ Нужно написать: coins или bucks")
        return

    await state.update_data(currency=currency)
    await state.set_state(AddProduct.amount)
    await message.answer("Введите количество:")

@dp.message(AddProduct.amount)
async def set_amount(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(amount=message.text.strip())
    await state.set_state(AddProduct.price)
    await message.answer("Введите цену (числом):")

@dp.message(AddProduct.price)
async def set_price(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    if not message.text.strip().isdigit():
        await message.answer("❌ Цена должна быть числом. Пример: 199")
        return

    data = await state.get_data()
    add_product(data["currency"], data["amount"], int(message.text.strip()))

    await state.clear()
    await message.answer("✅ Товар добавлен", reply_markup=admin_menu())

# ====== УДАЛЕНИЕ ТОВАРА ======
# ВАЖНО: нужна функция get_all_products() в database.py (я ниже напишу, что добавить)
@dp.callback_query(F.data == "delete_product")
async def delete_product_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    products = get_all_products()

    if not products:
        await callback.answer("Товаров нет", show_alert=True)
        return

    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(
            text=f"❌ {p[1]} | {p[2]} | {p[3]}₽",
            callback_data=f"del_{p[0]}"
        )])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin_back")])

    await callback.message.edit_text(
        "Выбери товар для удаления:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@dp.callback_query(F.data.startswith("del_"))
async def delete_product_action(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    product_id = int(callback.data.split("_")[1])
    delete_product(product_id)

    await callback.answer("Удалено ✅")
    await callback.message.edit_text("👑 Админ панель:", reply_markup=admin_menu())

# ====== ЗАКАЗЫ (заглушка) ======
@dp.callback_query(F.data == "orders")
async def orders(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("📋 Раздел заказов пока не реализован.", reply_markup=admin_menu())

# ====== WEBHOOK STARTUP/SHUTDOWN ======
async def on_startup(app: web.Application):
    if not WEBHOOK_URL:
        logging.error("APP_URL не задан. Добавь APP_URL в Render Environment (например https://xxx.onrender.com)")
        return
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(app: web.Application):
    await bot.delete_webhook(drop_pending_updates=False)
    await bot.session.close()
    logging.info("Webhook удалён, сессия закрыта")

# ====== HTTP APP (порт для Render) ======
def build_app() -> web.Application:
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # endpoint для webhook
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    # healthcheck чтобы Render видел что сервис жив
    async def health(request):
        return web.Response(text="OK")

    app.router.add_get("/", health)
    return app

if __name__ == "__main__":
    app = build_app()
    port = int(os.getenv("PORT", "10000"))
    web.run_app(app, host="0.0.0.0", port=port)




