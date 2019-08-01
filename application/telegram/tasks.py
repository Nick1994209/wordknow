import logging

from app.models import User
from app.utils import get_datetime_now
from telegram import constants
from telegram.utils import generate_markup, get_learn_repeat_markup, safe_send_message

logger = logging.getLogger('telegram_tasks')


def notify_repetition():
    logger.info('Start notify_repetition')

    if not can_run_task():
        logger.info('End (time) notify_repetition')
        return

    now = get_datetime_now()
    users = User.objects.filter(
        status=User.Status.FREE,
        learned_words__start_repetition_time__lt=now,
        learningstatus__repetition_notified__isnull=True,
    ).select_related('learningstatus').distinct()

    logger.info('get users %d', users.count())

    for user in users.iterator():
        safe_send_message(
            user,
            'Hello, my friend! Do you want to repeat new words?',
            markup=generate_markup(constants.Handlers.repetition.path),
        )
        user.learningstatus.update_notification_time(get_datetime_now())

    logger.info('End notify_repetition')


def notify_learning():
    logger.info('Start notify_learning')

    if not can_run_task():
        logger.info('End (time) notify_learning')
        return

    for user in User.objects.iterator():
        safe_send_message(
            user,
            'Hi! I want to suggest learning new words) Давай, изучи пару слов!',
            markup=get_learn_repeat_markup(),
        )
    logger.info('End notify_learning')


def can_run_task():
    now = get_datetime_now()

    logger.info('Current time %s', now)

    hours_from, hours_to = 10, 22
    if hours_from <= now.hour <= hours_to:
        return True

    logger.info('My time is not got! %s', now)
    return False
