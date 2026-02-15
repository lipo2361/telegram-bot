import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import BOT_TOKEN, ADMIN_ID, BOT_USERNAME
from database import *

print("BOT_TOKEN starts with:", str(BOT_TOKEN)[:10])
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


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


def back():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])


def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_product")],
        [InlineKeyboardButton(text="❌ Удалить товар", callback_data="delete_product")],
        [InlineKeyboardButton(text="📋 Заказы", callback_data="orders")]
    ])


# ====== START ======
@dp.message(F.text.startswith("/start"))
async def start(message: Message):
    args = message.text.split()
    ref = int(args[1]) if len(args) > 1 else None

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
        caption="💳Оплатите, выбранную вами цену и пришлите чек💸\n\n🌐Обязательно перед оплатой выключите Vpn✅"
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

    await callback.message.edit_text(text, reply_markup=back())


# ====== НАЗАД ======
@dp.callback_query(F.data == "back")
async def go_back(callback: CallbackQuery):
    await callback.message.edit_text("Главное меню 👇", reply_markup=main_menu())


# ====== АДМИН ПАНЕЛЬ ======
@dp.message(F.text == "/admin")
async def admin(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Админ панель:", reply_markup=admin_menu())


@dp.callback_query(F.data == "add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddProduct.currency)
    await callback.message.answer("Введите тип: coins или bucks")


@dp.message(AddProduct.currency)
async def set_currency(message: Message, state: FSMContext):
    await state.update_data(currency=message.text)
    await state.set_state(AddProduct.amount)
    await message.answer("Введите количество:")


@dp.message(AddProduct.amount)
async def set_amount(message: Message, state: FSMContext):
    await state.update_data(amount=message.text)
    await state.set_state(AddProduct.price)
    await message.answer("Введите цену:")


@dp.message(AddProduct.price)
async def set_price(message: Message, state: FSMContext):
    data = await state.get_data()
    add_product(data["currency"], data["amount"], int(message.text))
    await state.clear()
    await message.answer("✅ Товар добавлен")


# ====== ЗАПУСК ======
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

