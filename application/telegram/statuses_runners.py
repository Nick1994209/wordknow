import logging
from abc import ABC, abstractmethod

import telebot
from django.db.transaction import atomic

from app.models import User, WordStatus
from app.utils import get_datetime_now
from telegram import constants
from telegram.utils import send_message, get_success_text, get_learn_repeat_markup, generate_markup

logger = logging.getLogger(__name__)


class BaseRunner(ABC):
    def __init__(self, message: telebot.types.Message, user: User):
        self.message = message
        self.user = user

    @abstractmethod
    def first_run(self):
        pass

    @abstractmethod
    def run(self):
        pass


class LearnWordRunner(BaseRunner):
    @atomic()
    def first_run(self):
        self.user.update_status(User.Status.LEARNING)
        send_message(
            self.user, 'Изучать слова это здоворо! Приступим!' + constants.Emogies.astronaut,
        )
        self.choice_next_word()

    @atomic
    def run(self):
        self.set_learn_word(self.message.text)
        self.choice_next_word()

    def choice_next_word(self):
        learning_status = self.user.learning_status

        # набрали слов. Пора заканчивать
        if learning_status.count_words <= len(learning_status.repeat_words.all()):
            self.user.update_status(User.Status.FREE)
            message = '%s Отлично! Самое время повторить слова! %s' % (
                constants.Emogies.rocket, constants.Emogies.rocket,
            )
            send_message(self.user, message, generate_markup(constants.Handlers.repetition.path))
            return

        word = learning_status.next_learn_word
        if not word:
            send_message(
                self.user,
                '%s Вы изучили все слова! Можно добавить еще слова для изучения! %s %s ' % (
                    get_success_text(), constants.Emogies.fearful, constants.Emogies.astonished,
                ),
            )
            self.user.update_status(User.Status.FREE)
            send_message(
                self.user,
                'Не хотите повторить изученное? %s' % constants.Emogies.astronaut,
                markup=generate_markup(constants.Handlers.learn_words.path,
                                       constants.Handlers.repetition.path),
            )
            return

        send_message(
            self.user, word.learn_text,
            markup=generate_markup(
                constants.Commands.learn, constants.Commands.miss, constants.Handlers.stop.path,
            ),
        )

    def set_learn_word(self, message_text: str) -> bool:
        word = self.user.learning_status.next_learn_word
        if not word:
            logger.info('for user %s, end words', self.user.username)
            return True

        if message_text == constants.Commands.learn:  # Устанавливаем слово
            ws = WordStatus.objects.create(
                user_id=self.user.id, word=word, start_repetition_time=get_datetime_now(),
            )
            self.user.learning_status.repeat_words.add(ws)
            self.user.learning_status.set_next_learn_word()
        elif message_text == constants.Commands.miss:
            self.user.learning_status.set_next_learn_word()
        else:
            send_message(
                self.user, 'Не понятное сообщение. Вы хотите выучить слово?',
                markup=generate_markup(
                    constants.Commands.learn, constants.Commands.miss, constants.Handlers.stop.path,
                ),
            )
            return False
        return True


class RepeatWord(BaseRunner):
    @atomic
    def first_run(self):
        self.user.update_status(User.Status.REPETITION)

        send_message(self.user, 'Повторять слова это здоворо! Приступим! Введите перевод:')
        learning_status = self.user.learning_status
        # all repeated words set how repeated =)
        learning_status.set_complete_repetition_words(with_last_repeated=True)

        repetition_words = WordStatus.objects.filter(
            user=self.user, start_repetition_time__lt=get_datetime_now(),
        ).exclude(
            id__in=[status_word.id for status_word in learning_status.repeat_words.all()],
        )
        self.user.learning_status.repeat_words.add(*repetition_words)


    @atomic
    def run(self, is_first_run=False):
        if self.guess():
            self.repeat()

    def repeat(self, start_repetition=False):
        # start_repetition - если мы только начинаем повторять слова, то ставит в True
        learning_status = self.user.learning_status

        next_word_status = learning_status.get_next_repeat_word_status(start_repetition)
        if not next_word_status:
            learning_status.update_notification_time(None)
            learning_status.set_complete_repetition_words()

            send_message(
                self.user,
                'My congratulations! Вы повторили все слова ' + constants.Emogies.fearful,
                markup=get_learn_repeat_markup(),
            )
            self.user.update_status(User.Status.FREE)
            return

        learning_status.set_repetition_word_status_id(next_word_status.id)
        send_message(self.user, next_word_status.get_word_for_translating())

    def guess(self) -> bool:
        guess_translated = self.message.text
        repetition_word_status = self.user.learning_status.repetition_word_status
        if repetition_word_status is None:
            return True

        if repetition_word_status.is_word_guessed(guess_translated):
            send_message(self.user, get_success_text())
            return True

        repetition_word_status.increase_not_guess()
        text = '%s \n Повторение - мать учения %s! \n Пожалуйста, напишите translate слова: "%s"' % (
            repetition_word_status.word,
            constants.Emogies.astonished,
            repetition_word_status.get_word_for_translating(),
        )

        send_message(self.user, text)
        return False
