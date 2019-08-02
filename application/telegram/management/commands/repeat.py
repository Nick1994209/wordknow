from django.db.transaction import atomic

from app.models import User
from app.utils import BaseCommandWithAutoreload
from telegram.statuses_runners import RepeatWord


# ДЛЯ дебага
class Command(BaseCommandWithAutoreload):
    @atomic
    def main(self, *args, **options):
        user = User.objects.get()
        RepeatWord(message=None, user=user).first_run()
