# -*- coding: utf-8 -*-
# Modified for pyTelegramBotAPI (https://github.com/eternnoir/pyTelegramBotAPI/)
# https://github.com/botanio/sdk/blob/master/botan.py


import json

import requests

from project import settings

TRACK_URL = 'https://api.botan.io/track'


# Эту функцию можно модифицировать, чтобы собирать...
# ...именно то, что нужно (или вообще ничего)
def make_json(message):
    data = {}
    data['message_id'] = message.message_id
    data['from'] = {}
    data['from']['id'] = message.from_user.id
    if message.from_user.username is not None:
        data['from']['username'] = message.from_user.username
    data['chat'] = {}
    # Chat.Id используется в обоих типах чатов
    data['chat']['id'] = message.chat.id
    return data


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
        # set up for a retry, or continue in a retry loop
        return False
    except (requests.exceptions.RequestException, ValueError) as e:
        # catastrophic error
        print(e)
        return False


def botan_tracking(func):
    def wrap(message):
        func(message)
        track(settings.BOTAN_API_KEY, message.chat.id, message, func.__name__)
    return wrap