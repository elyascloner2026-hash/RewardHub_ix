import asyncio
import os
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database import (
    init_db,
    add_user,
    get_user,
    give_channel_reward,
    claim_daily,
)

from keyboards.menu import main_menu


TOKEN = os.getenv("BOT_TOKEN")

print("BOT_TOKEN exists:", TOKEN is not None)
print("BOT_TOKEN length:", len(TOKEN) if TOKEN else 0)

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing")


bot = Bot(token=TOKEN)
dp = Dispatcher()


# =========================
# کانال‌های اجباری
# =========================

REQUIRED_CHANNELS = [
    "@vip_funy",
    "@game_chanell_vip",
]


# =========================
# گیفت‌ها
# =========================

GIFTS = {
    1: {
        "name": "🎁 گیفت معمولی",
        "cost": 50,
    },
    2: {
        "name": "🎁 گیفت ویژه",
        "cost": 100,
    },
    3: {
        "name": "🎁 گیفت خفن",
        "cost": 250,
    },
}


# =========================
# دیتابیس درخواست گیفت
# =========================

async def init_gifts_db():
    db = await aiosqlite.connect("database.db")

    await db.execute("""
        CREATE TABLE IF NOT EXISTS gift_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            gift_id INTEGER NOT NULL,
            gift_name TEXT NOT NULL,
            cost INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)

    await db.commit()
    await db.close()


# =========================
# بررسی عضویت
# =========================

async def check_membership(user_id: int) -> bool:
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)

            if member.status in ("left", "kicked"):
                return False

        except Exception as e:
            print(f"Membership check error for {channel}: {e}")
            return False

    return True


# =========================
# کیبورد عضویت
# =========================

def join_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 عضویت در کانال اول",
                    url="https://t.me/vip_funy",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎮 عضویت در کانال دوم",
                    url="https://t.me/game_chanell_vip",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ بررسی عضویت",
                    callback_data="check_join",
                )
            ],
        ]
    )


# =========================
# کیبورد گیفت‌ها
# =========================

def gifts_keyboard():
    buttons = []

    for gift_id, gift in GIFTS.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{gift['name']} | ⭐ {gift['cost']}",
                callback_data=f"gift_{gift_id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🔙 بازگشت",
            callback_data="back_menu",
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# =========================
# منوی اصلی
# =========================

async def send_main_menu(message: Message):
    user = await get_user(message.from_user.id)

    if not user:
        await message.answer(
            "❌ حساب شما پیدا نشد.\n"
            "لطفاً دوباره /start را بزنید."
        )
        return

    # ساختار جدید:
    # user[0] = user_id
    # user[1] = username
    # user[2] = referrals
    # user[3] = balance

    referrals = user[2]
    points = user[3]

    await message.answer(
        "🎁 به RewardHub خوش آمدید!\n\n"
        f"⭐ امتیاز: {points}\n"
        f"👥 رفرال: {referrals}\n\n"
        "از منوی زیر انتخاب کن:",
        reply_markup=main_menu(),
    )


# =========================
# /start
# =========================

@dp.message(CommandStart())
async def start(message: Message):

    user_id = message.from_user.id
    username = message.from_user.username

    # بررسی عضویت
    is_member = await check_membership(user_id)

    if not is_member:
        await message.answer(
            "🔒 برای استفاده از RewardHub باید در هر دو کانال عضو باشید.\n\n"
            "1️⃣ کانال اول را باز کن\n"
            "2️⃣ کانال دوم را باز کن\n"
            "3️⃣ عضو هر دو شو\n"
            "4️⃣ روی «بررسی عضویت» بزن\n\n"
            "🎁 بعد از تأیید عضویت، ۵ امتیاز دریافت می‌کنی.",
            reply_markup=join_keyboard(),
        )
        return

    # گرفتن رفرال
    args = (message.text or "").split(maxsplit=1)

    referral_id = None

    if len(args) > 1:
        try:
            referral_id = int(args[1])
        except ValueError:
            referral_id = None

    if referral_id == user_id:
        referral_id = None

    # ساخت کاربر
    is_new_user = await add_user(
        user_id,
        username,
        referral_id
    )

    # پاداش عضویت کانال
    await give_channel_reward(user_id)

    await send_main_menu(message)


# =========================
# بررسی عضویت
# =========================

@dp.callback_query(F.data == "check_join")
async def check_join(callback: CallbackQuery):

    user_id = callback.from_user.id
    username = callback.from_user.username

    is_member = await check_membership(user_id)

    if not is_member:
        await callback.answer(
            "❌ هنوز در هر دو کانال عضو نیستید.",
            show_alert=True,
        )
        return

    # اگر کاربر وجود نداشته باشد، بساز
    await add_user(
        user_id,
        username,
        None
    )

    # پاداش ۵ امتیازی عضویت
    reward_given = await give_channel_reward(user_id)

    if reward_given:
        text = (
            "✅ عضویت شما تأیید شد!\n\n"
            "🎉 ۵ امتیاز بابت عضویت دریافت کردی."
        )
    else:
        text = (
            "✅ عضویت شما تأیید شد!\n\n"
            "ℹ️ امتیاز عضویت قبلاً دریافت شده است."
        )

    await callback.answer(
        "✅ عضویت تأیید شد!",
        show_alert=True,
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.message.answer(
        text
    )

    await send_main_menu(callback.message)


# =========================
# پروفایل
# =========================

@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):

    user = await get_user(callback.from_user.id)

    if not user:
        await callback.answer(
            "ابتدا /start را بزنید.",
            show_alert=True
        )
        return

    user_id = user[0]
    username = user[1]
    referrals = user[2]
    points = user[3]

    username_text = (
        f"@{username}"
        if username
        else "ندارد"
    )

    await callback.message.edit_text(
        "👤 حساب شما\n\n"
        f"🆔 آیدی: {user_id}\n"
        f"👤 نام کاربری: {username_text}\n"
        f"⭐ امتیاز: {points}\n"
        f"👥 رفرال: {referrals}",
        reply_markup=main_menu(),
    )

    await callback.answer()


# =========================
# امتیازات
# =========================

@dp.callback_query(F.data == "points")
async def points(callback: CallbackQuery):

    user = await get_user(callback.from_user.id)

    if not user:
        await callback.answer(
            "ابتدا /start را بزنید.",
            show_alert=True
        )
        return

    points_value = user[3]

    await callback.answer(
        f"⭐ امتیاز شما: {points_value}",
        show_alert=True
    )


# =========================
# رفرال
# =========================

@dp.callback_query(F.data == "referral")
async def referral(callback: CallbackQuery):

    me = await bot.get_me()

    link = (
        f"https://t.me/{me.username}"
        f"?start={callback.from_user.id}"
    )

    await callback.message.edit_text(
        "🔗 لینک دعوت شما:\n\n"
        f"{link}\n\n"
        "👥 هر رفرال معتبر = ⭐ ۱۰ امتیاز\n\n"
        "لینک را برای دوستانت بفرست و امتیاز بگیر!",
        reply_markup=main_menu(),
    )

    await callback.answer()


# =========================
# آمار
# =========================

@dp.callback_query(F.data == "stats")
async def stats(callback: CallbackQuery):

    user = await get_user(callback.from_user.id)

    if not user:
        await callback.answer(
            "ابتدا /start را بزنید.",
            show_alert=True
        )
        return

    referrals = user[2]
    points = user[3]

    await callback.message.edit_text(
        "📊 آمار شما\n\n"
        f"👥 تعداد رفرال: {referrals}\n"
        f"⭐ امتیاز فعلی: {points}\n\n"
        "💡 هر رفرال معتبر ۱۰ امتیاز دارد.",
        reply_markup=main_menu(),
    )

    await callback.answer()


# =========================
# پاداش روزانه
# =========================

@dp.callback_query(F.data == "daily")
async def daily(callback: CallbackQuery):

    user_id = callback.from_user.id

    user = await get_user(user_id)

    if not user:
        await callback.answer(
            "ابتدا /start را بزنید.",
            show_alert=True
        )
        return

    success = await claim_daily(user_id)

    if success:
        await callback.answer(
            "🎉 ۱۰ امتیاز روزانه دریافت کردی!",
            show_alert=True
        )

        await callback.message.edit_text(
            "🎉 پاداش روزانه دریافت شد!\n\n"
            "⭐ +۱۰ امتیاز به حساب شما اضافه شد.",
            reply_markup=main_menu(),
        )

    else:
        await callback.answer(
            "⏳ پاداش روزانه را قبلاً دریافت کردی.\n"
            "فردا دوباره امتحان کن.",
            show_alert=True
        )


# =========================
# صفحه گیفت‌ها
# =========================

@dp.callback_query(F.data == "gifts")
async def gifts(callback: CallbackQuery):

    user = await get_user(callback.from_user.id)

    if not user:
        await callback.answer(
            "ابتدا /start را بزنید.",
            show_alert=True
        )
        return

    points = user[3]

    await callback.message.edit_text(
        "🎁 فروشگاه گیفت\n\n"
        f"⭐ امتیاز شما: {points}\n\n"
        "یکی از گیفت‌های زیر را انتخاب کن:",
        reply_markup=gifts_keyboard(),
    )

    await callback.answer()


# =========================
# خرید گیفت
# =========================

@dp.callback_query(F.data.startswith("gift_"))
async def buy_gift(callback: CallbackQuery):

    try:
        gift_id = int(callback.data.split("_")[1])
    except Exception:
        await callback.answer(
            "❌ گیفت نامعتبر است.",
            show_alert=True
        )
        return

    if gift_id not in GIFTS:
        await callback.answer(
            "❌ این گیفت وجود ندارد.",
            show_alert=True
        )
        return

    gift = GIFTS[gift_id]

    user_id = callback.from_user.id

    user = await get_user(user_id)

    if not user:
        await callback.answer(
            "ابتدا /start را بزنید.",
            show_alert=True
        )
        return

    points = user[3]

    if points < gift["cost"]:
        await callback.answer(
            f"❌ امتیاز کافی نداری.\n\n"
            f"⭐ امتیاز شما: {points}\n"
            f"💰 قیمت گیفت: {gift['cost']}",
            show_alert=True
        )
        return

    await callback.message.edit_text(
        "🎁 تأیید دریافت گیفت\n\n"
        f"{gift['name']}\n"
        f"💰 قیمت: {gift['cost']} امتیاز\n"
        f"⭐ موجودی شما: {points}\n\n"
        "برای تأیید روی دکمه زیر بزن:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ تأیید دریافت",
                        callback_data=f"confirm_gift_{gift_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 برگشت",
                        callback_data="gifts",
                    )
                ],
            ]
        ),
    )

    await callback.answer()


# =========================
# تأیید گیفت
# =========================

@dp.callback_query(F.data.startswith("confirm_gift_"))
async def confirm_gift(callback: CallbackQuery):

    try:
        gift_id = int(callback.data.split("_")[2])
    except Exception:
        await callback.answer(
            "❌ خطا.",
            show_alert=True
        )
        return

    if gift_id not in GIFTS:
        await callback.answer(
            "❌ گیفت نامعتبر است.",
            show_alert=True
        )
        return

    gift = GIFTS[gift_id]
    user_id = callback.from_user.id

    db = await aiosqlite.connect("database.db")

    try:
        cursor = await db.execute(
            """
            SELECT balance
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        )

        row = await cursor.fetchone()

        if not row:
            await callback.answer(
                "❌ حساب پیدا نشد.",
                show_alert=True
            )
            return

        balance = row[0]

        if balance < gift["cost"]:
            await callback.answer(
                "❌ امتیاز کافی نیست.",
                show_alert=True
            )
            return

        # کم کردن امتیاز
        await db.execute(
            """
            UPDATE users
            SET balance = balance - ?
            WHERE user_id = ?
            """,
            (gift["cost"], user_id)
        )

        # ثبت درخواست گیفت
        await db.execute(
            """
            INSERT INTO gift_requests
            (user_id, gift_id, gift_name, cost, status)
            VALUES (?, ?, ?, ?, 'pending')
            """,
            (
                user_id,
                gift_id,
                gift["name"],
                gift["cost"],
            )
        )

        await db.commit()

    finally:
        await db.close()

    await callback.message.edit_text(
        "🎉 درخواست گیفت ثبت شد!\n\n"
        f"🎁 {gift['name']}\n"
        f"⭐ هزینه: {gift['cost']} امتیاز\n\n"
        "⏳ درخواست شما در انتظار بررسی است.",
        reply_markup=main_menu(),
    )

    await callback.answer(
        "✅ درخواست ثبت شد!",
        show_alert=True
    )


# =========================
# بازگشت به منو
# =========================

@dp.callback_query(F.data == "back_menu")
async def back_menu(callback: CallbackQuery):

    user = await get_user(callback.from_user.id)

    if not user:
        await callback.answer(
            "ابتدا /start را بزنید.",
            show_alert=True
        )
        return

    points = user[3]
    referrals = user[2]

    await callback.message.edit_text(
        "🎁 به RewardHub خوش آمدید!\n\n"
        f"⭐ امتیاز: {points}\n"
        f"👥 رفرال: {referrals}\n\n"
        "از منوی زیر انتخاب کن:",
        reply_markup=main_menu(),
    )

    await callback.answer()


# =========================
# اجرای بات
# =========================

async def main():

    await init_db()
    await init_gifts_db()

    print("RewardHub is running...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
