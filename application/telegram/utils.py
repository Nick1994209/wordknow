import logging
from random import choice as random_choice

import telebot
from django.conf import settings

from app.models import User
from app.utils import retry_if_false, safe_str
from telegram.exceptions import SendMessageException

from . import constants
from .bot import bot

logger = logging.getLogger(__name__)


@retry_if_false(attempts_count=5, sleep_time=0.1, use_logging=True)
def safe_send_message(user: User, text: str, markup=None, parse_mode=None) -> bool:
    if settings.TELEGRAM_DEBUG:
        logger.info('User=%d SEND MESSAGE=%s', user.id, safe_str(text))
        return True

    try:
        bot.send_message(user.chat_id, text, reply_markup=markup, parse_mode=parse_mode)
        return True
    except telebot.apihelper.ApiException as e:
        logger.info('User=%s cant send message: api_exception=%s, msg=%s', user.username, e, text)
        return False
    except Exception as e:
        logger.exception('User=%s cant send message: base exception=%sm msg=%s',
                         user.username, e, text)
        return False


def send_message(user: User, text: str, markup=None, parse_mode=None):
    if not safe_send_message(user, text, markup=markup, parse_mode=parse_mode):
        raise SendMessageException()


def generate_markup(*items):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for item in items:
        markup.add(item)
    return markup


def get_learn_repeat_markup():
    return generate_markup(
        constants.Handlers.learn_words.path,
        constants.Handlers.repetition.path,
        constants.Handlers.help.path,
    )


def get_user(message: telebot.types.Message) -> User:
    user, is_created = User.objects.get_or_create(
        chat_id=message.chat.id,
        defaults=dict(
            username=message.from_user.username,
        ),
    )
    if is_created:
        logger.info('Added new user chat_id=%s, username=%s', user.chat_id, user.username)

    if user.username != message.from_user.username:
        user.username = message.from_user.username
        user.save(update_fields=('username',))
    return user


def get_success_text() -> str:
    texts = [
        'Огонь!', 'Вперед! В том же духе)', 'Кто у нас тут такой молодец?)', 'Ну ничоси выдаешь!',
        'Краусава!', 'Где же вы были раньше?)', 'Не переродились еще на Руси!',
    ]
    return random_choice(texts)


def request_logger(func):
    def wrap(message):
        logger.info(
            'Received message by handler=%s chat_id=%s text=%s',
            func.__name__, message.chat.id, safe_str(message.text),
        )
        func(message)
    return wrap
