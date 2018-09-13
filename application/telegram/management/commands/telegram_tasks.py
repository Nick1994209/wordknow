import logging

import schedule
from django.core.management.base import BaseCommand
from django.utils import autoreload

from telegram import tasks

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        autoreload.main(self.main)

    def main(self):
        schedule.every(5).minutes.do(tasks.notify_repetition)
        schedule.every(5).hours.do(tasks.notify_learning)

        while True:
            try:
                schedule.run_pending()
            except Exception:
                logger.exception('Scheduler tasks run: exception')
