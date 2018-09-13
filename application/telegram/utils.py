import logging
from random import choice as random_choice

import telebot

from app.models import LearningStatus, User, WordStatus
from app.utils import get_datetime_now

from .bot import bot
from .constants import Commands, Emogies, Handlers

logger = logging.getLogger(__name__)


def choice_next_learning_word(user: User):
    learning_status = user.learning_status

    # набрали слов. Пора заканчивать
    if learning_status.count_words <= len(learning_status.repeat_words.all()):
        user.update_status(User.Status.FREE)
        message = '%s Отлично! Самое время повторить слова! %s' % (Emogies.rocket, Emogies.rocket)
        bot.send_message(
            user.chat_id, message, reply_markup=generate_markup(Handlers.repetition.path),
        )
        return

    word = learning_status.next_learn_word
    if not word:
        bot.send_message(
            user.chat_id,
            '%s Вы изучили все слова! Можно добавить еще слова для изучения! %s %s ' % (
                get_success_text(), Emogies.fearful, Emogies.astonished,
            ),
        )
        user.update_status(User.Status.FREE)
        bot.send_message(
            user.chat_id,
            'Не хотите повторить изученное? %s' % Emogies.astronaut,
            reply_markup=generate_markup(Handlers.learn_words.path, Handlers.repetition.path),
        )
        return

    bot.send_message(
        user.chat_id, word.learn_text,
        reply_markup=generate_markup(Commands.learn, Commands.miss, Handlers.stop.path),
    )


def set_learn_word(message: telebot.types.Message, user: User) -> bool:
    word = user.learning_status.next_learn_word
    if not word:
        logger.info('for user %s, end words', user.username)
        return True

    if message.text == Commands.learn:
        # устанавливаем слово
        ws = WordStatus.objects.create(
            user_id=user.id, word=word, start_repetition_time=get_datetime_now(),
        )
        user.learning_status.repeat_words.add(ws)
        user.learning_status.set_next_learn_word()
    elif message.text == Commands.miss:
        # пропускаем слово
        user.learning_status.set_next_learn_word()
    else:
        # когда ввели не учить/пропустить
        bot.send_message(
            user.chat_id, 'Не понятное сообщение. Вы хотите выучить слово?',
            reply_markup=generate_markup(Commands.learn, Commands.miss, Handlers.stop.path),
        )
        return False
    return True


def repeat_word(user: User, start_repetition=False):
    # start_repetition - если мы только начинаем повторять слова, то ставит в True
    learning_status = user.learning_status

    next_word_status = learning_status.get_next_repeat_word_status(start_repetition)
    if not next_word_status:
        learning_status.update_notification_time(None)
        learning_status.set_complete_repetition_words()

        bot.send_message(
            user.chat_id,
            'My congratulations! Вы повторили все слова ' + Emogies.fearful,
            reply_markup=get_learn_repeat_markup(),
        )
        user.update_status(User.Status.FREE)
        return

    learning_status.set_repetition_word_status_id(next_word_status.id)
    bot.send_message(user.chat_id, next_word_status.get_text_for_translating())


def guess_word(message: telebot.types.Message, user: User) -> bool:
    guess_translated = message.text
    repetition_word_status = user.learning_status.repetition_word_status
    if repetition_word_status is None:
        return True

    if repetition_word_status.is_word_guessed(guess_translated):
        bot.send_message(user.chat_id, get_success_text())
        return True

    repetition_word_status.increase_not_guess()
    text = '%s \n Повторение - мать учения! Пожалуйста, напишите translate слова %s' % (
        repetition_word_status.word.learn_text, Emogies.astonished,
    )

    bot.send_message(user.chat_id, text)
    return False


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
