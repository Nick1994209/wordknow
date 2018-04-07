import logging
import typing
from datetime import timedelta

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
            self.date_updated = timezone.now()
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

    def __str__(self):
        return self.username

    @cached_property
    def learning_status(self) -> 'LearningStatus':
        status = (
            LearningStatus.objects.
                filter(user_id=self.id).
                prefetch_related('repeat_words').
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


class Word(CreatedUpdateBaseModel):
    text = models.CharField(max_length=256)
    translate = models.CharField(max_length=256)

    def __str__(self):
        return self.text + ' - ' + self.translate

    @property
    def learn_text(self):
        return self.text + ' - ' + self.translate


class WordStatus(CreatedUpdateBaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learned_words')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='learned_words')
    start_repetition_time = models.DateTimeField()
    count_repetitions = models.IntegerField(default=0)
    number_not_guess = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Статус изучения слова'
        ordering = ('id',)

    def __str__(self):
        return self.user.username + ' ' + self.word.text

    def increase_not_guess(self):
        self.number_not_guess += 1
        self.save(update_fields=('number_not_guess',))

    def set_next_repetition_time(self, from_time):
        times = {
            1: timedelta(hours=1),
            2: timedelta(hours=6),
            3: timedelta(days=1),
            4: timedelta(days=7),
            5: timedelta(days=30),
            6: timedelta(days=120),
        }
        default_delta = timedelta(days=3 * 120)
        self.count_repetitions += 1
        self.start_repetition_time = from_time + times.get(self.count_repetitions, default_delta)
        self.save(update_fields=('count_repetitions', 'start_repetition_time'))

        logger.info(
            'WordStatus %d %s update count_repetitions=%d time=%s',
            self.user_id, self.word.text, self.count_repetitions, self.start_repetition_time,
        )


class LearningStatus(CreatedUpdateBaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    repeat_words = models.ManyToManyField(WordStatus)
    number_not_guess = models.IntegerField(default=0)
    count_words = models.IntegerField(default=5)

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

    def get_repetition_word_status(self) -> typing.Union[WordStatus, None]:
        if not self.repetition_word_status_id:
            return None

        word_statuses = [
            ws for ws in self.repeat_words.all() if ws.id == self.repetition_word_status_id
        ]
        if len(word_statuses) != 1:
            logger.error('WTF. %s; repetition_id = %d ', word_statuses, self.id)
            raise Exception('Как так? Я тут не должен был оказаться')
        return word_statuses[0]

    def set_repetition_word_status_id(self, word_status_id):
        logger.info(
            'LearningStatus %d update repetition_word_status_id %d',
            self.user_id, word_status_id,
        )
        self.repetition_word_status_id = word_status_id
        self.save(update_fields=('repetition_word_status_id',))

    @property
    def next_learn_word(self) -> typing.Union[Word, None]:
        from_word_id = self.learn_word_id or 0
        return Word.objects.filter(id__gt=from_word_id).first()

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
            'LearningStatus %d update next_learn_word: current=%d next=%d',
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
        self.save(update_fields=('repetition_notified', ))

    def set_complete_repetition_words(self):
        next_repeat_word_status = self.get_next_repeat_word_status()
        last_repeat_id = next_repeat_word_status and next_repeat_word_status.id or float('Inf')

        update_repeat_words = filter(lambda w: w.id < last_repeat_id, self.repeat_words.all())
        now = get_datetime_now()
        for word_status in update_repeat_words:
            word_status.set_next_repetition_time(now)
        self.repeat_words.clear()
