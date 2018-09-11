from django.core.management.base import BaseCommand
from django.utils import autoreload

from telegram import handlers


class Command(BaseCommand):
    def handle(self, *args, **options):
        autoreload.main(handlers.start)
