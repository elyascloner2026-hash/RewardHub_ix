from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 حساب من",
                    callback_data="profile"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔗 لینک رفرال",
                    callback_data="referral"
                ),
                InlineKeyboardButton(
                    text="⭐ امتیازات",
                    callback_data="points"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 دریافت گیفت",
                    callback_data="gifts"
                ),
                InlineKeyboardButton(
                    text="🎉 پاداش روزانه",
                    callback_data="daily"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 آمار رفرال",
                    callback_data="stats"
                )
            ]
        ]
    )
