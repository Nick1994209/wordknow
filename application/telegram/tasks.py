import threading
import logging
import time

from app.utils import get_datetime_now
from telegram.constants import Handlers
from telegram.utils import generate_markup
from .bot import bot

from app.models import User, WordStatus

logger = logging.getLogger('telegram_tasks')


def start_background_tasks():
    # threading.Thread(target=start_tasks).start()
    start_tasks()


def start_tasks():
    logger.info('start telegram tasks')
    while True:
        try:
            notification_users_with_repetition_time()
        except Exception as e:
            logger.error('background tasks error', e)
        time.sleep(30)


def notification_users_with_repetition_time():
    now = get_datetime_now()
    users = User.objects.filter(
        status=User.Status.FREE,
        learned_words__start_repetition_time__lt=now,
        learningstatus__repetition_notified__isnull=True,
    ).select_related('learningstatus').distinct()
    markup = generate_markup(Handlers.learn_words.path)
    for user in users:
        bot.send_message(
            user.chat_id,
            'Hello my friend! Do you want to repetition new words?',
            reply_markup=markup,
        )
        user.learningstatus.update_notification_time()