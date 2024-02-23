from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

from tgbot.plugins.basictextcommands import start, help, edit_help, about, edit_about
from tgbot.plugins.login import login, login_callback

bot = Client("satya", api_id=2171111, api_hash="fd7acd07303760c52dcc0ed8b2f73086",
             bot_token="5154860805:AAEZs1rWayks2zJF4y1LeYoQb_r7ApDSMBU")

bot.add_handler(
    MessageHandler(
        start,
        filters.command('start')))
bot.add_handler(
    MessageHandler(
        help,
        filters.command('help')))
bot.add_handler(
    CallbackQueryHandler(
        edit_help,
        filters.regex('^/help$')))
bot.add_handler(
    CallbackQueryHandler(
        edit_about,
        filters.regex('^/about$')))

bot.add_handler(
    MessageHandler(
        about,
        filters.command(['about', 'note', 'warning'])))
# Login

bot.add_handler(
    MessageHandler(
        login,
        filters.command('login')))
bot.add_handler(
    CallbackQueryHandler(
        login_callback,
        filters.regex('^/login$'))

)