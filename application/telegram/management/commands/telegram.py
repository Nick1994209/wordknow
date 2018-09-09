from django.core.management.base import BaseCommand

from telegram import handlers


class Command(BaseCommand):
    def handle(self, *args, **options):
        handlers.start()
