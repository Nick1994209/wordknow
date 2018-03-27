from django.core.management.base import BaseCommand

from ...tasks import start_tasks


class Command(BaseCommand):
    def handle(self, *args, **options):
        start_tasks()
