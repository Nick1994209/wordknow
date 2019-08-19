import logging
from abc import ABC, abstractmethod

import telebot
from django.conf import settings
from django.db.transaction import atomic

from app.models import User, WordStatus
from app.utils import get_datetime_now
from telegram import constants
from telegram.utils import generate_markup, get_learn_repeat_markup, get_success_text, send_message

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
            send_message(
                self.user,
                f'Вы можете добавить слова на сайте {settings.BOT_SITE_URL}'
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
            return True
        elif message_text == constants.Commands.miss:
            self.user.learning_status.set_next_learn_word()
            return True
        else:
            send_message(
                self.user, 'Не понятное сообщение. Вы хотите выучить слово?',
                markup=generate_markup(
                    constants.Commands.learn, constants.Commands.miss, constants.Handlers.stop.path,
                ),
            )
            return False


class RepeatWord(BaseRunner):
    @atomic
    def first_run(self):
        self.user.update_status(User.Status.REPETITION)
        self.user.learning_status.add_words_for_repetition()
        self.repeat(start_repetition=True)

    @atomic
    def run(self):
        if self.guess():
            self.repeat()

    def repeat(self, start_repetition=False):
        """ Repeat word (send message to telegram)

        :param start_repetition: если мы только начинаем повторять слова, то ставим в True

        если есть слово для повторения:
            устанавливаем это слово как то, которое начали повторять
            отправляем пользователю сообщение с этим словом

        если нету слова для повторения:
            указываем, что можно пинговать пользователя о повторении слов
            обновляем время следующего повторения для повторенных слов
               и удаляем их из тех которые сейчас нужно повторять
            указываем, что нету следующего слова для повторения (ставим ему None)
            переводим пользователя в статус: FREE
        """
        learning_status = self.user.learning_status

        next_word_status = learning_status.get_next_repeat_word_status(start_repetition)
        if not next_word_status:
            send_message(
                self.user,
                'My congratulations! Вы повторили все слова ' + constants.Emogies.fearful,
                markup=get_learn_repeat_markup(),
            )
            self.user.update_status(User.Status.FREE)
            return

        if start_repetition:
            send_message(self.user, 'Повторять слова это здоворо! Приступим! Введите перевод:')

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
        text = ('%s\n'
                ' Пожалуйста, напишите translate слова: "%s"\n'
                ' Вы можете удалить это слово: %s')
        text = text % (
            repetition_word_status.word,
            repetition_word_status.get_word_for_translating(),
            constants.Handlers.delete_word.path,
        )

        send_message(self.user, text)
        return False
