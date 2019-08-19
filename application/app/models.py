import logging
import random
import typing
import uuid

from django.conf import settings
from django.db import models
from django.db.transaction import atomic
from django.utils.functional import cached_property

from app.utils import get_datetime_now, safe_str

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
        REPETITION = 'repetition'

        CHOICES = (
            (FREE, 'в свободном плавании'),
            (LEARNING, 'изучает новые слова'),
            (REPETITION, 'повторяет слова'),
        )

    chat_id = models.CharField(max_length=100, verbose_name='ID чата в телеграме', unique=True)
    username = models.CharField(max_length=100, verbose_name='ID чата в телеграме')
    status = models.CharField(max_length=50, choices=Status.CHOICES, default=Status.FREE)

    auth_code = models.CharField(
        max_length=10, null=True, verbose_name='Код для авторизации',
        help_text='Высылается в telegram при попытке авторизоваться',
    )
    auth_token = models.UUIDField(null=True)

    def __str__(self):
        return self.username

    @cached_property
    def learning_status(self) -> 'LearningStatus':
        status = (
            LearningStatus.objects
            .filter(user_id=self.id)
            .prefetch_related('repeat_words')
            .select_related('repetition_word_status', 'learn_word')
            .first()
        )
        if not status:
            status = LearningStatus.objects.create(user_id=self.id)
        return status

    @atomic
    def update_status(self, new_status):
        logger.debug('User=%s update status from %s - %s', self.id, self.status, new_status)
        self.perform_last_status_actions(old_status=self.status, new_status=new_status)
        self.status = new_status
        self.save(update_fields=('status',))

    def perform_last_status_actions(self, old_status, new_status):
        old_status = self.Status.REPETITION
        if old_status == self.Status.REPETITION:
            self.learning_status.update_notification_time()
            self.learning_status.clear_repeated_words()

    @property
    def is_free(self):
        return self.status == self.Status.FREE

    @property
    def is_learning(self):
        return self.status == self.Status.LEARNING

    @property
    def is_repetition(self):
        return self.status == self.Status.REPETITION

    def generate_auth_code(self):
        self.auth_code = str(random.randint(1000, 9999))
        self.save(update_fields=('auth_code',))

    def generate_auth_token(self):
        self.auth_token = uuid.uuid4()
        self.auth_code = None
        self.save(update_fields=('auth_token', 'auth_code'))


class Word(CreatedUpdateBaseModel):
    text = models.CharField(max_length=256)
    translate = models.CharField(max_length=256)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             null=True, verbose_name='Cлово пользователя')

    def __str__(self):
        return f'{self.text} - {self.translate}'

    @property
    def learn_text(self):
        return f'{self.text} - {self.translate}'


class WordStatus(CreatedUpdateBaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learned_words')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='learned_words')
    start_repetition_time = models.DateTimeField(
        null=True, blank=True, verbose_name='Время когда нужно будет повторить слово')
    count_repetitions = models.IntegerField(default=0, verbose_name='Количество повторений слова')
    number_not_guess = models.IntegerField(default=0, verbose_name='Сколько раз не угадал слово')

    class Meta:
        verbose_name = 'Статус изучения слова'
        ordering = ('id',)
        unique_together = ('user', 'word')

    def __str__(self):
        return f'WordStatus "{self.word}", user={self.user}'

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

        logger.debug(
            'WordStatus %d %s update count_repetitions=%d time=%s',
            self.user_id, safe_str(str(self.word)),
            self.count_repetitions, self.start_repetition_time,
        )

    @property
    def is_conversely(self):
        """
        Проверка статуса слова "наобарот"

        служит что бы показать, мы будем угадывать слово или перевод
        """
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
    repeat_words = models.ManyToManyField(WordStatus, blank=True, null=True)
    count_words = models.IntegerField(
        default=5, verbose_name='Количество слов, которые пользователь будет учить за раз')
    repetition_word_status = models.ForeignKey(
        WordStatus, on_delete=models.SET_NULL, blank=True, null=True, related_name='from_repetition',
        verbose_name='На этом слове остановились повторять',
    )
    learn_word = models.ForeignKey(
        Word, on_delete=models.SET_NULL, blank=True, null=True,
        verbose_name='На этом слове остановились изучать',
    )

    repetition_notified = models.DateTimeField(
        null=True, verbose_name='Когда оповещали о повторении слов',
    )  # TODO rename to repetition_notified_time

    class Meta:
        verbose_name = 'Статус пользователя повторения/изучения слов'

    def __str__(self):
        return self.user.username + ' learning_status'

    def set_repetition_word_status_id(self, word_status_id):
        logger.debug(
            'LearningStatus update: user=%s next repetition_word_status_id=%s',
            self.user_id, word_status_id,
        )
        self.repetition_word_status_id = word_status_id
        self.save(update_fields=('repetition_word_status_id',))

    @property
    def next_learn_word(self) -> typing.Optional[Word]:
        from_word_id = self.learn_word_id or 0

        # if user added words => return user word; else return general word
        user_word = Word.objects.filter(user_id=self.user_id, id__gt=from_word_id).first()
        if user_word:
            return user_word

        logger.debug('User=%s without words', self.user_id)
        return Word.objects.filter(user=None, id__gt=from_word_id).first()

    def get_next_repeat_word_status(self, start_repetition=False) -> typing.Optional[WordStatus]:
        """
        Возвращает следующее слово для повторения
        если больше нет слов для повторения => возвращает None
            (все слова были повторены или их не начинали повторять)
        """
        repetition_word_status_id = 0
        if self.repetition_word_status_id and not start_repetition:
            repetition_word_status_id = self.repetition_word_status_id

        # мы не фильтруем sql-ем т.k. это лишний запрос, а repeat_words.all() его не делает,
        # если до этого был prefetch
        next_repeat_words = filter(
            lambda x: x.id > repetition_word_status_id, self.repeat_words.all(),
        )
        next_repeat_words = sorted(next_repeat_words, key=lambda x: x.id)
        if next_repeat_words:
            return next_repeat_words[0]
        return None

    def set_next_learn_word(self):
        word = self.next_learn_word
        logger.debug(
            'LearningStatus user=%d update next_learn_word: current=%d next=%d',
            self.user_id, self.learn_word_id, word.id,
        )

        self.learn_word_id = word.id
        self.learn_word = word
        self.save(update_fields=('learn_word_id',))

    @property
    def is_words_were_repeated(self):
        return self.get_next_repeat_word_status() is None and self.learn_word_id

    def clear_repeated_words(self):
        """
        Очищаем список слов для повторения

        Всем повторенным словам устанавливаем следующее время для повторения
        Очищаем все слова для повторения
        Устанавливаем следующее слово для повторения в None
        """
        self.update_repetition_time_for_repeated_words()
        self.repeat_words.clear()
        self.set_repetition_word_status_id(None)

    def update_notification_time(self, time=None):
        """

        :param set_time:
        :return:
        """
        logger.debug(
            'LearningStatus for user=%d update notification_time: %s',
            self.user_id, time,
        )
        self.repetition_notified = time
        self.save(update_fields=('repetition_notified',))

    @atomic()
    def update_repetition_time_for_repeated_words(self):
        if self.is_words_were_repeated:
            next_repeat_id = float('Inf')
        elif self.repetition_word_status_id:
            next_repeat_id = self.repetition_word_status_id
        else:
            next_repeat_id = 0

        # делаем ручную фильтрацию вместо sql, т.k. до этого был выполнен prefetch_related,
        # который вытащил все repeat_words
        repeat_words = filter(lambda w: w.id < next_repeat_id, self.repeat_words.all())
        now = get_datetime_now()
        for word_status in repeat_words:
            word_status.set_next_repetition_time(now)

    @atomic()
    def update_repeated_words(self):
        next_repeat_word_status = self.get_next_repeat_word_status()
        # если нету следующего слова для повторения -> все слова были повторены
        # значит устанавливаем float(inf) - бесконечно большое число
        next_repeat_id = next_repeat_word_status and next_repeat_word_status.id or float('Inf')

        def check_words_were_repeated(w: WordStatus):
            """
            Проверка, что слово было повторено
            id слова, которое нужно повторять больше id, повторенного слова
            """
            return next_repeat_id > w.id

        # делаем ручную фильтрацию вместо sql, т.k. до этого был выполнен prefetch_related,
        # который вытащил все repeat_words
        repeat_words = filter(check_words_were_repeated, self.repeat_words.all())
        now = get_datetime_now()
        for word_status in repeat_words:
            word_status.set_next_repetition_time(now)

    def add_words_for_repetition(self):
        repetition_words = (
            WordStatus.objects
            .filter(user=self.user, start_repetition_time__lt=get_datetime_now())
            .exclude(id__in=[  # исключаем добавленные слова
                status_word.id for status_word in self.user.learning_status.repeat_words.all()
            ])
        )
        self.repeat_words.add(*repetition_words)
