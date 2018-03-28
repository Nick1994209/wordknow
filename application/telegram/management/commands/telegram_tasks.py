import logging

from django.core.management.base import BaseCommand

from telegram import tasks

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('task', type=str)

    def handle(self, *args, **options):
        background_tasks = {
            'notify_repetition': tasks.notify_repetition,
            'notify_learning': tasks.notify_learning,
        }
        background_tasks.get(options['task'], lambda: logger.exception('Task not found'))()
