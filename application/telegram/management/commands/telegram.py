from django.core.management.base import BaseCommand

from ...handlers import start


class Command(BaseCommand):
    def handle(self, *args, **options):
        start()
