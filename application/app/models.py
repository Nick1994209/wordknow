import logging
import random
import typing
import uuid

from django.conf import settings
from django.db import models
from django.db.transaction import atomic
from django.utils import timezone
from django.utils.functional import cached_property

from app.utils import get_datetime_now

logger = logging.getLogger(__name__)


class CreatedUpdateBaseModel(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def save(self, update_fields=None, **kwargs):
        if update_fields:
            update_fields = set(update_fields)
            self.date_updated = get_datetime_now()
            update_fields.add('date_updated')
            update_fields = tuple(update_fields)
        super().save(update_fields=update_fields, **kwargs)

    class Meta:
        abstract = True


class User(CreatedUpdateBaseModel):
    class Status:
        FREE = 'free'
        LEARNING = 'learning'
        REPETITION = 'learning_status'

        CHOICES = (
            (FREE, 'в свободном плавании'),
            (LEARNING, 'изучает новые слова'),
            (REPETITION, 'повторяет слова'),
        )

    chat_id = models.CharField(max_length=100, verbose_name='ID чата в телеграме', unique=True)
    username = models.CharField(max_length=100, verbose_name='ID чата в телеграме')
    status = models.CharField(max_length=50, choices=Status.CHOICES, default=Status.FREE)

    auth_code = models.CharField(
        max_length=10, default='', verbose_name='Код для авторизации',
        help_text='Высылается в telegram при попытке авторизоваться',
    )
    auth_token = models.UUIDField(null=True)

    def __str__(self):
        return self.username

    @cached_property
    def learning_status(self) -> 'LearningStatus':
        status = (
            LearningStatus.objects.
                filter(user_id=self.id).
                prefetch_related('repeat_words').
                select_related('repetition_word_status').
                first()
        )
        if not status:
            status = LearningStatus.objects.create(user_id=self.id)
        return status

    @atomic
    def update_status(self, status):
        logger.info('User %s update status from %s - %s', self.username, self.status, status)
        if status == self.status:
            return

        self.perform_last_status_actions(old_status=self.status)
        self.status = status
        self.save(update_fields=('status',))

    def perform_last_status_actions(self, old_status):
        if old_status == self.Status.REPETITION:
            self.learning_status.set_complete_repetition_words()

    def status_is_free(self):
        return self.status == self.Status.FREE

    def status_is_learning(self):
        return self.status == self.Status.LEARNING

    def status_is_repetition(self):
        return self.status == self.Status.REPETITION

    def generate_auth_code(self):
        self.auth_code = str(random.randint(1000, 9999))

        self.auth_code = '1111'
        self.save(update_fields=('auth_code',))

    def generate_auth_token(self):
        self.auth_token = uuid.uuid4()
        self.save(update_fields=('auth_token',))


class Word(CreatedUpdateBaseModel):
    text = models.CharField(max_length=256)
    translate = models.CharField(max_length=256)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             null=True, verbose_name='Cлово пользователя')

    def __str__(self):
        return self.text + ' - ' + self.translate

    @property
    def learn_text(self):
        return self.text + ' - ' + self.translate


class WordStatus(CreatedUpdateBaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learned_words')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='learned_words')
    start_repetition_time = models.DateTimeField(
        null=True, verbose_name='Время когда нужно будет повторить слово')
    count_repetitions = models.IntegerField(default=0, verbose_name='Количество повторений слова')
    number_not_guess = models.IntegerField(default=0, verbose_name='Сколько раз не угадал слово')

    class Meta:
        verbose_name = 'Статус изучения слова'
        ordering = ('id',)

    def __str__(self):
        return self.user.username + ' ' + self.word.text

    def increase_not_guess(self):
        self.number_not_guess += 1
        self.save(update_fields=('number_not_guess',))

    def set_next_repetition_time(self, from_time):
        self.count_repetitions += 1

        next_repetition_time = settings.REPETITION_TIMES.get(self.count_repetitions)
        if next_repetition_time:
            self.start_repetition_time = from_time + next_repetition_time
        else:
            self.start_repetition_time = None
        self.save(update_fields=('count_repetitions', 'start_repetition_time'))

        logger.info(
            'WordStatus %d %s update count_repetitions=%d time=%s',
            self.user_id, self.word.text, self.count_repetitions, self.start_repetition_time,
        )

    @property
    def is_conversely(self):
        # служит что бы показать, мы будем угадывать слово или перевод
        return self.count_repetitions % 2

    def is_word_guessed(self, message: str):
        check_word = self.get_translated_word()
        return check_word.lower().strip() == message.lower().strip()

    def get_word_for_translating(self):
        return self.word.text if self.is_conversely else self.word.translate

    def get_translated_word(self):
        return self.word.translate if self.is_conversely else self.word.text


class LearningStatus(CreatedUpdateBaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    repeat_words = models.ManyToManyField(WordStatus)
    count_words = models.IntegerField(
        default=5, verbose_name='Количество слов, которые пользователь будет учить за раз')
    repetition_word_status = models.ForeignKey(
        WordStatus, on_delete=models.SET_NULL, null=True, related_name='from_repetition',
        verbose_name='На этом слове остановились повторять',
    )
    learn_word = models.ForeignKey(
        Word, on_delete=models.SET_NULL, null=True,
        verbose_name='На этом слове остановились изучать',
    )

    repetition_notified = models.DateTimeField(
        null=True, verbose_name='Когда оповещали о повторении слов',
    )

    class Meta:
        verbose_name = 'Статус пользователя повторения/изучения слов'

    def __str__(self):
        return self.user.username + ' learning_status'

    def set_repetition_word_status_id(self, word_status_id):
        logger.info(
            'LearningStatus update: user=%d next repetition_word_status_id=%d',
            self.user_id, word_status_id,
        )
        self.repetition_word_status_id = word_status_id
        self.save(update_fields=('repetition_word_status_id',))

    @property
    def next_learn_word(self) -> typing.Union[Word, None]:
        from_word_id = self.learn_word_id or 0

        # if user added words => return user word; else return general word
        user_word = Word.objects.filter(user_id=self.user_id, id__gt=from_word_id).first()
        if user_word:
            return user_word

        logger.info('User=%s without words', self.user_id)
        return Word.objects.filter(user=None, id__gt=from_word_id).first()

    def get_next_repeat_word_status(self, start_repetition=False) -> typing.Union[WordStatus, None]:

        if start_repetition:
            repetition_word_status_id = 0
        else:
            repetition_word_status_id = self.repetition_word_status_id

        next_repeat_words = filter(
            lambda x: x.id > repetition_word_status_id, self.repeat_words.all(),
        )
        next_repeat_words = sorted(next_repeat_words, key=lambda x: x.id)
        if next_repeat_words:
            return next_repeat_words[0]
        return None

    def set_next_learn_word(self):
        word = self.next_learn_word
        logger.info(
            'LearningStatus user=%d update next_learn_word: current=%d next=%d',
            self.user_id, self.learn_word_id, word.id,
        )

        self.learn_word_id = word.id
        self.learn_word = word
        self.save(update_fields=('learn_word_id',))

    def update_notification_time(self, set_time=None):
        logger.info(
            'LearningStatus %d update notification_time: %s',
            self.user_id, set_time,
        )
        self.repetition_notified = set_time
        self.save(update_fields=('repetition_notified',))

    def set_complete_repetition_words(self):
        next_repeat_word_status = self.get_next_repeat_word_status()
        last_repeat_id = next_repeat_word_status and next_repeat_word_status.id or float('Inf')

        update_repeat_words = filter(lambda w: w.id < last_repeat_id, self.repeat_words.all())
        now = get_datetime_now()
        for word_status in update_repeat_words:
            word_status.set_next_repetition_time(now)
        self.repeat_words.clear()
