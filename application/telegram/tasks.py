import logging

from app.models import User
from app.utils import get_datetime_now
from telegram.constants import Handlers
from telegram.utils import generate_markup

from .bot import bot

logger = logging.getLogger('telegram_tasks')


def notify_repetition():
    logger.info('start notify_repetition')

    now = get_datetime_now()
    users = User.objects.filter(
        status=User.Status.FREE,
        learned_words__start_repetition_time__lt=now,
        learningstatus__repetition_notified__isnull=True,
    ).select_related('learningstatus').distinct()

    logger.info('get users %d', users.count())

    markup = generate_markup(Handlers.repetition.path)
    for user in users.iterator():
        bot.send_message(
            user.chat_id,
            'Hello my friend! Do you want to repetition new words?',
            reply_markup=markup,
        )
        user.learningstatus.update_notification_time(get_datetime_now())

    logger.info('end notify_repetition')


def notify_learning():
    logger.info('start notify_learning')

    now = get_datetime_now()
    hours_from, hours_to = 10, 22
    if not (hours_from <= now.hour <= hours_to):
        logger.info('My time is not got! %s', now)
        return

    markup = generate_markup(Handlers.learn_words.path)
    for user in User.objects.iterator():
        bot.send_message(
            user.chat_id,
            'Hi! I want to suggest learning new words) Давай, изучи пару слов!',
            reply_markup=markup,
        )

    logger.info('end notify_learning')
