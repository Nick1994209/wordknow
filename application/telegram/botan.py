# coding: utf8
# Modified for pyTelegramBotAPI (https://github.com/eternnoir/pyTelegramBotAPI/)
# https://github.com/botanio/sdk/blob/master/botan.py
import logging

import requests

from app.utils import retry_if_false, safe_str
from project import settings

TRACK_URL = 'https://api.botan.io/track'

logger = logging.getLogger(__name__)


class Botan:
    @retry_if_false(attempts_count=3, sleep_time=0.01)
    @classmethod
    def track(cls, uid, message, name='Message'):
        if not settings.BOTAN_API_KEY:
            return

        msg = cls.make_json(message)

        try:
            r = requests.post(
                TRACK_URL,
                params={"token": settings.BOTAN_API_KEY, "uid": uid, "name": name},
                data=msg,
                headers={'Content-type': 'application/json'},
            )
            return r.json()
        except requests.exceptions.Timeout:
            return False
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.exception('botan exception: %s', e)
            return False

    @staticmethod
    def make_json(message):
        data = {
            'message_id': message.message_id,
            'from': {
                'id': message.from_user.id,
            },
            'chat': {
                'id': message.chat.id,
            },
        }
        if message.from_user.username is not None:
            data['from']['username'] = message.from_user.username
        return data


def botan_track(func):
    def wrap(message):
        logger.info(
            'Received message by handler=%s chat_id=%s text=%s',
            func.__name__, message.chat.id, safe_str(message.text),
        )
        func(message)
        Botan.track(message.chat.id, message, func.__name__)
    return wrap
