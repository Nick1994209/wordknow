import logging
from random import choice as random_choice

import telebot
from django.conf import settings

from app.models import User
from app.utils import retry_if_false, safe_str
from telegram.exceptions import SendMessageException

from .bot import bot
from .constants import Commands, Emogies, Handlers

logger = logging.getLogger(__name__)


@retry_if_false(attempts_count=5, sleep_time=0.1, use_logging=True)
def safe_send_message(user: User, text: str, markup=None) -> bool:
    if settings.TELEGRAM_DEBUG:
        logger.info('User=%d SEND MESSAGE=%s', user.id, safe_str(text))
        return True

    try:
        bot.send_message(user.chat_id, text, reply_markup=markup)
        return True
    except telebot.apihelper.ApiException as e:
        logger.info('User=%s cant send message: api_exception=%s', user.username, e)
        return False
    except Exception as e:
        logger.exception('User=%s cant send message: base exception=%s', user.username, e)
        return False


def send_message(user: User, text: str, markup=None):
    if not safe_send_message(user, text, markup):
        raise SendMessageException()


def generate_markup(*items):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for item in items:
        markup.add(item)
    return markup


def get_learn_repeat_markup():
    return generate_markup(Handlers.learn_words.path, Handlers.repetition.path)


def get_user(message: telebot.types.Message):
    try:
        user, _ = User.objects.get_or_create(
            chat_id=message.chat.id, username=message.from_user.username,
        )
    except Exception as e:
        logger.exception(e)
        user = User.objects.get(chat_id=message.chat.id)
    return user


def get_success_text() -> str:
    texts = [
        'Огонь!', 'Вперед! В том же духе)', 'Кто у нас тут такой молодец?)', 'Ну ничоси выдаешь!',
        'Краусава!', 'Где же вы были раньше?)', 'Не переродились еще на Руси!',
    ]
    return random_choice(texts)

# class TelegramHandler:
#     def __init__(self, message):
#         self.message = message
#
#     def handle(self, message: telebot.types.Message):
#         raise NotImplemented
#
#     @classmethod
#     def set_handler(cls, bot: telebot.TeleBot, command):
#         message_handler = cls.get_handler()
#
#         commands = command if isinstance(command, (list, tuple)) else [command]
#         bot.message_handler(commands=commands)(message_handler)
#
#     @classmethod
#     def get_handler(cls):
#         @wraps(cls)
#         def handle(message: telebot.types.Message):
#             self = cls(message)
#             self.handle(message)
#         return handle
#
#
# class BaseHandler(TelegramHandler):
#     def __init__(self, message):
#         self.user = get_user(message)
#         super().__init__(message)
#
#     @classmethod
#     def get_handler(cls):
#         handler = super().get_handler()
#         return botan_track(handler)

# class LearnWordsHandler(BaseHandler):
#     @atomic()
#     def handle(self, message: telebot.types.Message):
#         self.user.update_status(User.Status.LEARNING)
#         send_message(self.user, 'Изучать слова это здоворо! Приступим!' + constants.Emogies.astronaut)
#         self.user.learning_status.repeat_words.clear()
#         LearningWord.choice_next_word(self.user)
#
#
# LearnWordsHandler.set_handler(bot, command=constants.Handlers.learn_words.handler)
