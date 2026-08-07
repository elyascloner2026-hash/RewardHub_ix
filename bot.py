import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from database import init_db, add_user, add_referral, get_user
from keyboards.menu import main_menu


TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    args = message.text.split(maxsplit=1)
    referral_id = None

    if len(args) > 1:
        try:
            referral_id = int(args[1])
        except ValueError:
            referral_id = None

    is_new_user = await add_user(
        user_id,
        username,
        referral_id
    )

    if is_new_user and referral_id:
        await add_referral(referral_id, user_id)

    user = await get_user(user_id)

    points = user[2] if user else 0
    referrals = user[3] if user else 0

    me = await bot.get_me()

    await message.answer(
        "🎁 به RewardHub خوش آمدید!\n\n"
        f"⭐ امتیاز: {points}\n"
        f"👥 رفرال: {referrals}/5\n\n"
        "برای شروع از منوی زیر استفاده کنید:",
        reply_markup=main_menu()
    )


@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)

    if not user:
        await callback.answer("ابتدا /start را بزنید.", show_alert=True)
        return

    await callback.message.edit_text(
        "👤 حساب شما\n\n"
        f"🆔 آیدی: {user[0]}\n"
        f"⭐ امتیاز: {user[2]}\n"
        f"👥 رفرال: {user[3]}/5",
        reply_markup=main_menu()
    )

    await callback.answer()


@dp.callback_query(F.data == "points")
async def points(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)

    points = user[2] if user else 0

    await callback.answer(
        f"⭐ امتیاز شما: {points}",
        show_alert=True
    )


@dp.callback_query(F.data == "referral")
async def referral(callback: CallbackQuery):
    me = await bot.get_me()

    link = f"https://t.me/{me.username}?start={callback.from_user.id}"

    await callback.message.edit_text(
        "🔗 لینک رفرال شما:\n\n"
        f"{link}\n\n"
        "👥 هر رفرال معتبر = ۱۰ امتیاز\n"
        "💰 برای برداشت حداقل ۵ رفرال لازم است.",
        reply_markup=main_menu()
    )

    await callback.answer()


@dp.callback_query(F.data == "stats")
async def stats(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)

    referrals = user[3] if user else 0

    await callback.answer(
        f"📊 رفرال‌های شما: {referrals}/5",
        show_alert=True
    )


@dp.callback_query(F.data == "withdraw")
async def withdraw(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)

    if not user:
        await callback.answer(
            "ابتدا /start را بزنید.",
            show_alert=True
        )
        return

    referrals = user[3]

    if referrals < 5:
        await callback.answer(
            f"❌ برای برداشت باید ۵ رفرال داشته باشید.\n"
            f"وضعیت فعلی: {referrals}/5",
            show_alert=True
        )
        return

    await callback.answer(
        "✅ درخواست برداشت ثبت شد.\n"
        "نسخه فعلی آزمایشی است و پرداخت واقعی انجام نمی‌شود.",
        show_alert=True
    )


async def main():
    await init_db()

    print("RewardHub is running...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
