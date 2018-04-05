# coding: utf8
# Modified for pyTelegramBotAPI (https://github.com/eternnoir/pyTelegramBotAPI/)
# https://github.com/botanio/sdk/blob/master/botan.py
import logging

import requests

from project import settings

TRACK_URL = 'https://api.botan.io/track'

logger = logging.getLogger(__name__)


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


# add retrying
def track(token, uid, message, name='Message'):
    try:
        r = requests.post(
            TRACK_URL,
            params={"token": token, "uid": uid, "name": name},
            data=make_json(message),
            headers={'Content-type': 'application/json'},
        )
        return r.json()
    except requests.exceptions.Timeout:
        return False
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.exception('botan exception: %s', e)
        return False


def botan_track(func):
    def wrap(message):
        func(message)
        if settings.BOTAN_API_KEY:
            track(settings.BOTAN_API_KEY, message.chat.id, message, func.__name__)
        logger.info(
            'Handler: %s chat_id: %s text: %s',
            func.__name__, str(message.chat.id), message.text,
        )

    return wrap


def safe_str(obj):
    try:
        return obj.encode('utf-8')
    except UnicodeEncodeError:
        return obj.encode('ascii', 'ignore').decode('ascii')
    except:
        return ""
