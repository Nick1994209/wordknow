import logging

from django.core.management.base import BaseCommand

from ...tasks import notify_learning, notify_repetition

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('task', type=str)

    def handle(self, *args, **options):
        tasks = {
            'notify_repetition': notify_repetition,
            'notify_learning': notify_learning,
        }
        tasks.get(options['task'], lambda: logger.exception('Task not found'))()
