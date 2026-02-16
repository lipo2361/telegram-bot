import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN, ADMIN_ID
from database import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ================= СОСТОЯНИЯ =================
class AddProduct(StatesGroup):
    currency = State()
    amount = State()
    price = State()


# ================= КЛАВИАТУРЫ =================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡Купить голду 🛍️", callback_data="coins")],
        [InlineKeyboardButton(text="🎁 Купить Battle pass 🛍️", callback_data="bucks")],
        [InlineKeyboardButton(text="🤝 Партнёрская программа", callback_data="ref")]
    ])


def back_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])


def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_product")],
        [InlineKeyboardButton(text="❌ Удалить товар", callback_data="delete_product")],
        [InlineKeyboardButton(text="📋 Заказы", callback_data="orders")]
    ])


# ================= START =================
@dp.message(F.text.startswith("/start"))
async def start(message: Message):
    add_user(message.from_user.id)

    photo = FSInputFile("banner.jpg")

    text = """
⚡Zews Gold Shop🛍️

👋 Привет  - Это Zews Gold и его помощник Зевс 😎Он же - Крут в своем деле 🔥
Сколько голды купишь на этот раз?🛍️

🔥 Для продолжения нажми на кнопку  ⚡Купить голду

⁉️ Если есть вопросы, то пиши их мне - @ZewsGold_Support
"""

    await message.answer_photo(photo, caption=text, reply_markup=main_menu())


# ================= НАЗАД =================
@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    photo = FSInputFile("banner.jpg")

    await callback.message.delete()
    await callback.message.answer_photo(photo, caption="""
⚡Zews Gold Shop🛍️

👋 Привет  - Это Zews Gold и его помощник Зевс 😎Он же - Крут в своем деле 🔥
Сколько голды купишь на этот раз?🛍️

🔥 Для продолжения нажми на кнопку  ⚡Купить голду

⁉️ Если есть вопросы, то пиши их мне - @ZewsGold_Support
""", reply_markup=main_menu())


# ================= ПАРТНЕРКА =================
@dp.callback_query(F.data == "ref")
async def referral(callback: CallbackQuery):
    photo = FSInputFile("banner.jpg")

    await callback.message.delete()
    await callback.message.answer_photo(
        photo,
        caption="🤝 Получайте 25% с каждой покупки друга!",
        reply_markup=back_button()
    )


# ================= COINS =================
@dp.callback_query(F.data == "coins")
async def coins(callback: CallbackQuery):
    products = get_products("coins")
    photo = FSInputFile("coins.jpg")

    buttons = []
    for p in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"G {p[2]} ┃ {p[3]}₽",
                callback_data=f"buy_{p[0]}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])

    await callback.message.delete()
    await callback.message.answer_photo(
        photo,
        caption="Выберите тариф голды:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


# ================= BUCKS =================
@dp.callback_query(F.data == "bucks")
async def bucks(callback: CallbackQuery):
    products = get_products("bucks")
    photo = FSInputFile("bucks.jpg")

    buttons = []
    for p in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"{p[2]} ┃ {p[3]}₽",
                callback_data=f"buy_{p[0]}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])

    await callback.message.delete()
    await callback.message.answer_photo(
        photo,
        caption="Выберите Battle Pass:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


# ================= ЗАКАЗ =================
@dp.callback_query(F.data.startswith("buy_"))
async def buy(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    product = get_product(product_id)

    order_id = create_order(callback.from_user.id, product_id, product[3])
    photo = FSInputFile("order.jpg")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплата по СБП", callback_data=f"pay_{order_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])

    await callback.message.delete()
    await callback.message.answer_photo(
        photo,
        caption=f"{product[2]}\nК оплате: {product[3]}₽",
        reply_markup=keyboard
    )


# ================= ОПЛАТА =================
@dp.callback_query(F.data.startswith("pay_"))
async def pay(callback: CallbackQuery):
    await callback.message.answer_photo(
        FSInputFile("qr.jpg"),
        caption="Оплатите и отправьте чек"
    )


# ================= ЧЕК =================
@dp.message(F.photo)
async def check_handler(message: Message):
    orders = get_pending_orders()
    if not orders:
        return

    order = orders[-1]
    order_id = order[0]

    username = f"@{message.from_user.username}" if message.from_user.username else "Нет username"

    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"🧾 Заказ #{order_id}\n👤 {username}\n🆔 {message.from_user.id}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"approve_{order_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{order_id}")
            ]
        ])
    )

    await message.answer("Чек отправлен на проверку ✅")


# ================= ПОДТВЕРЖДЕНИЕ =================
@dp.callback_query(F.data.startswith("approve_"))
async def approve(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    order = get_order(order_id)

    update_order_status(order_id, "approved")
    await bot.send_message(order[1], "Оплата подтверждена ✅")
    await callback.message.edit_caption("Оплата подтверждена ✅")


@dp.callback_query(F.data.startswith("reject_"))
async def reject(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    order = get_order(order_id)

    update_order_status(order_id, "rejected")
    await bot.send_message(order[1], "Оплата отклонена ❌")
    await callback.message.edit_caption("Оплата отклонена ❌")


# ================= АДМИН =================
@dp.message(F.text == "/admin")
async def admin(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Админ панель:", reply_markup=admin_menu())


@dp.callback_query(F.data == "orders")
async def show_orders(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    orders = get_pending_orders()
    if not orders:
        await callback.answer("Нет заказов", show_alert=True)
        return

    for o in orders:
        await callback.message.answer(f"Заказ #{o[0]} | ID {o[1]}")


# ================= ЗАПУСК =================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
