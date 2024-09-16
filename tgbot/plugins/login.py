import string
import random

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import connect_to_database


async def login(client, message):
    await message.reply(
        "Click below button to get login Link.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔑 Login", callback_data="/login")]]
        ),
    )


def generate_random_string(length):
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


async def login_callback(client, query):
    _hash = generate_random_string(16)
    state = generate_random_string(8)
    user_id = query.from_user.id
    db = await connect_to_database()
    await db.tg_sessions.insert_one(
        {
            "user_id": user_id,
            "_hash": _hash,
            "state": state,
            "message_id": query.message.id,
        }
    )
    await query.message.edit_text(
        "Please login to the bot by clicking the button below.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔑 Login",
                        url=f"https://apiauth.devh.in/auth/connect?app=telegram@devh.in?app=telegram&_hash={_hash}=&state={state}",
                    )
                ]
            ]
        ),
    )
