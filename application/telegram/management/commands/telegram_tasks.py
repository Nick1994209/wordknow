import logging

import schedule
from django.core.management.base import BaseCommand

from telegram import tasks

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):

        schedule.every(6).hours.do(tasks.notify_repetition)
        schedule.every(6).hours.do(tasks.notify_learning)

        while True:
            try:
                schedule.run_pending()
            except Exception:
                logger.exception('Scheduler tasks run: exception')
