import logging
import time

import telebot
from django.db.transaction import atomic

from app.models import User, Word
from project import settings
from telegram.utils import send_message

from . import constants
from .bot import bot
from .botan import botan_track
from .statuses_runners import LearnWordRunner, RepeatWord, get_learn_repeat_markup
from .utils import get_user

logger = logging.getLogger('telegram_handlers')


def start():
    logger.info('Start telegram bot')

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logger.exception(e)
        time.sleep(5)
        logger.info('RESTART')


@bot.message_handler(commands=['start', constants.Handlers.help.handler, 'go'])
@botan_track
def start_handler(message: telebot.types.Message):
    message_resp = 'Добро пожаловать! Для изучения английских слов вам поможет бот {} {}'.format(
        settings.TELEGRAM_BOT_NAME, constants.Emogies.wink
    )
    user = get_user(message)

    if user.status == User.Status.LEARNING:
        message_resp += '\n Сейчас Вы находитесь в стадии заучивания новых слов :)'
    elif user.status == User.Status.REPETITION:
        message_resp += '\n Сейчас Вы находитесь в стадии повторения слов :)'
    else:
        message_resp += ('\n Вы можете добавить слова которые хотите изучить на сайте %s'
                         % settings.BOT_SITE_URL)
    send_message(user, message_resp, markup=get_learn_repeat_markup())


@bot.message_handler(commands=[constants.Handlers.learn_words.handler])
@botan_track
def learn_words_handler(message: telebot.types.Message):
    user = get_user(message)
    LearnWordRunner(message=message, user=user).first_run()


@bot.message_handler(commands=[constants.Handlers.repetition.handler])
@botan_track
def repeat_words_handler(message: telebot.types.Message):
    user = get_user(message)
    RepeatWord(message=message, user=user).first_run()


@bot.message_handler(commands=[constants.Handlers.delete_word.handler])
@botan_track
def delete_word_handler(message: telebot.types.Message):
    user = get_user(message)

    if not user.is_repetition:
        send_message(user, 'Не понятна :( что Вы хотите? ' + constants.Handlers.help.path)

    word_status = user.learning_status.repetition_word_status
    if word_status:
        user.update_status(User.Status.FREE)

        send_message(user, '  Прощай "%s".' % word_status.word)
        word_status.delete()
        logger.info(f'word_status=%s was deleted', word_status)

    RepeatWord(message=message, user=user).first_run()


@bot.message_handler(commands=[constants.Handlers.stop.handler])
@botan_track
@atomic
def stop_handler(message: telebot.types.Message):
    user = get_user(message)
    user.update_status(user.Status.FREE)
    send_message(
        user, 'Да! Вы вольная птица). Чем Вы теперь хотите заняться?',
        get_learn_repeat_markup(),
    )


@bot.message_handler(content_types=["text"])
@botan_track
def text_handler(message: telebot.types.Message):
    user = get_user(message)
    if user.is_free:
        send_message(user, 'Не понятна :( что Вы хотите? ' + constants.Handlers.help.path)
    elif user.is_learning:
        LearnWordRunner(message=message, user=user).run()
    elif user.is_repetition:
        RepeatWord(message=message, user=user).run()
    else:
        raise Exception('User status not found: %s', user.status)


@bot.inline_handler(lambda query: True)
def query_text(query):
    """
    query_text handler will invoke when users insert @telegram_bot to another chat
    """
    last_word = Word.objects.filter(user_id=None).last()

    text = ''
    if last_word:
        text = last_word.learning_text
    else:
        logger.warning("DON'T HAVE GENERAL WORDS")

    start_text = "{} I'm learning words! And you? {}".format(
        settings.TELEGRAM_BOT_NAME, constants.Emogies.wink
    )
    single_msg = telebot.types.InlineQueryResultArticle(
        id="1", title=text[:200],
        input_message_content=telebot.types.InputTextMessageContent(
            message_text=start_text + text,
        ),
    )
    bot.answer_inline_query(query.id, results=[single_msg])
