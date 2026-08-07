import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from database import init_db, add_user, add_referral, get_user


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

    await message.answer(
        "🎁 به RewardHub خوش آمدید!\n\n"
        f"⭐ امتیاز شما: {points}\n"
        f"👥 رفرال‌های شما: {referrals}\n\n"
        "🔗 لینک رفرال شما:\n"
        f"https://t.me/{(await bot.get_me()).username}?start={user_id}\n\n"
        "💡 برای فعال شدن برداشت، حداقل ۵ رفرال معتبر لازم است."
    )


async def main():
    await init_db()

    print("RewardHub is running...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
