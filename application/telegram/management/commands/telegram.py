from app.utils import BaseCommandWithAutoreload
from telegram import handlers


class Command(BaseCommandWithAutoreload):
    def main(self, *args, **options):
        handlers.start()
