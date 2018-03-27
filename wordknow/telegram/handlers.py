import logging
import time

import telebot
from django.db.transaction import atomic

from app.models import User, Word, WordStatus
from app.utils import get_datetime_now
from project import settings

from .bot import bot
from .botan import botan_tracking
from .constants import Handlers
from .utils import (
    choice_next_learning_word, generate_markup, get_user, guess_word, repeat_word, set_learn_word,
    get_learn_repeat_markup,
)

logger = logging.getLogger(__name__)


def start():
    logger.info('Start telegram bot')

    if settings.DEBUG:
        bot.polling(none_stop=True)
        return

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logger.error(e)
        time.sleep(5)


@bot.message_handler(commands=['start', Handlers.help.handler, 'go'])
@botan_tracking
def start_handler(message: telebot.types.Message):
    chat_id = message.chat.id
    send_message = '''
        Добро пожаловать!
    '''
    user = get_user(message)

    if user.status == User.Status.LEARNING:
        send_message += '\n Вы сейчас находитесь в стадии заучивания новых слов :)'
    if user.status == User.Status.REPETITION:
        send_message += '\n Вы сейчас находитесь в стадии повторения слов :)'
    bot.send_message(chat_id, send_message, reply_markup=get_learn_repeat_markup())


@bot.message_handler(commands=[Handlers.learn_words.handler])
@botan_tracking
@atomic
def learn_words_handler(message):
    user = get_user(message)
    user.update_status(User.Status.LEARNING)
    bot.send_message(message.chat.id, 'Изучать слова это здоворо! Приступим!')
    user.learning_status.repeat_words.clear()
    choice_next_learning_word(user)


@bot.message_handler(commands=[Handlers.repetition.handler])
@botan_tracking
@atomic
def repeat_words_handler(message):
    user = get_user(message)
    user.update_status(User.Status.REPETITION)

    bot.send_message(message.chat.id, 'Повторять слова это здоворо! Приступим! Введите перевод:')
    learning_status = user.learning_status
    repetition_words = WordStatus.objects.filter(
        user=user, start_repetition_time__lt=get_datetime_now(),
    ).exclude(
        id__in=[status_word.id for status_word in learning_status.repeat_words.all()],
    )
    user.learning_status.repeat_words.add(*repetition_words)

    repeat_word(user, start_repetition=True)


@bot.message_handler(commands=[Handlers.stop.handler])
@botan_tracking
@atomic
def stop_handler(message):
    user = get_user(message)
    user.update_status(user.Status.FREE)
    bot.send_message(
        user.chat_id,
        'Да! Вы вольная птица). Чем вы теперь хотите заняться?',
        reply_markup=get_learn_repeat_markup(),
    )


@bot.message_handler(content_types=["text"])
@botan_tracking
@atomic
def text_handler(message):
    user = get_user(message)
    if user.status_is_free():
        bot.send_message(message.chat.id, 'Не понятна что вы хотите :(, ' + Handlers.help.path)
    elif user.status_is_learning():
        set_learn_word(message, user)
        choice_next_learning_word(user)
    elif user.status_is_repetition():
        if guess_word(message, user):
            repeat_word(user)
    else:
        raise Exception('User status not found: %s', user.status)


@bot.inline_handler(lambda query: True)
def query_text(query):
    last_word = Word.objects.last()
    if last_word:
        text = last_word.learn_text
    else:
        text = 'Words not append to db'

    start_text = settings.TELEGRAM_NAME + " I'm learning words! And you? "

    single_msg = telebot.types.InlineQueryResultArticle(
        id="1", title=text[:200],
        input_message_content=telebot.types.InputTextMessageContent(
            message_text=start_text + text,
        ),
    )
    bot.answer_inline_query(query.id, results=[single_msg])
