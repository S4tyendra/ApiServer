from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


async def start(client, message):
    await message.reply(
        "Hi! I am intelligent bot! developed by [satya](t.me/me_satyendra)!\nSee /help and /note",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📚 Help", callback_data="/help")],
                [InlineKeyboardButton("🚶 Developer", callback_data="/about")],
                [InlineKeyboardButton("📢 Channel", url="https://t.me/DevhUpdates")],
                [InlineKeyboardButton("👥 Group", url="https://t.me/devh_chat")],
            ]
        ),
    )


help_message = """
**Here are the commands you can use:**

**General Commands:**
`/start` - <i>Start the bot</i>
`/help` - <i>Show this message</i>
`/about` - <i>About the developer</i>

**Account Management:**
`/login` - <i>Login to the bot</i>
`/logout` - <i>Logout from the bot</i>
`/me` - <i>Get your profile</i>
`/credits` - <i>Get your credits</i>

**Purchasing:**
`/buy` - <i>Buy credits</i>

**Additional Resources:**
`/docs` - <i>Get the documentation</i>
"""


async def help(client, message):
    if not help_message:  # Basic error handling
        await message.reply("Help message is not configured.")
        return

    await message.reply(
        f"{help_message}",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📢 Channel", url="https://t.me/DevhUpdates")],
                [InlineKeyboardButton("👥 Group", url="https://t.me/devh_chat")],
            ]
        ),
    )


async def edit_help(client, query):
    await query.message.edit_text(
        f"{help_message}",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📢 Channel", url="https://t.me/DevhUpdates")],
                [InlineKeyboardButton("👥 Group", url="https://t.me/devh_chat")],
            ]
        ),
    )


about_message = """
**About:**
This bot is a Telegram client for [Devh](https://devh.in) API. Use this bot to access the API and retrieve the data you need.

**Note:**
- Please do not misuse the bot; it may result in a ban, and you won't be able to use the bot again.
- Avoid spamming or flooding the API with requests to prevent a ban.
- On the first login, you'll receive 5 free credits to access the API. Afterward, you need to buy credits.
- All requests are logged and monitored; misuse leads to an immediate ban.
- Content/data provided by the bot is property of [Devh](https://devh.in); commercial use without permission is prohibited.

**Developer:** [Satyendra](https://t.me/s4tyendra)
**Channel:** [DevhUpdates](https://t.me/DevhUpdates)
**Group:** [Devh Chat](https://t.me/devh_chat)
**How to use:** [Click here](https://api.devh.in/howtouse)
**Bot Documentation:** [Click here](https://api.devh.in/botdocs)
**Site:** [Devh](https://devh.in)
**API Documentation:** [Click here](https://api.devh.in/docs)
"""


async def about(client, message):
    await message.reply(
        about_message,
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📢 Channel", url="https://t.me/DevhUpdates")],
                [InlineKeyboardButton("👥 Group", url="https://t.me/devh_chat")],
            ]
        ),
    )


async def edit_about(client, query):
    await query.message.edit_text(
        about_message,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📢 Channel", url="https://t.me/DevhUpdates")],
                [InlineKeyboardButton("👥 Group", url="https://t.me/devh_chat")],
            ]
        ),
    )
