import logging

import schedule

from app.utils import BaseCommandWithAutoreload
from telegram import tasks

logger = logging.getLogger(__name__)


class Command(BaseCommandWithAutoreload):
    def main(self):
        schedule.every(5).minutes.do(tasks.notify_repetition)
        schedule.every(5).hours.do(tasks.notify_learning)

        while True:
            try:
                schedule.run_pending()
            except Exception:
                logger.exception('Scheduler tasks run: exception')
