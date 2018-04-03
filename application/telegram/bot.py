import telebot

from project import settings

bot = telebot.TeleBot(settings.TELEGRAM_BOT_KEY, threaded=False)
