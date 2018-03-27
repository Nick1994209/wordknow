from collections import namedtuple


class Handlers:
    Handler = namedtuple('Handler', ('handler', 'path'))
    learn_words = Handler('learn_words', '/learn_words')
    repetition = Handler('repetition', '/repetition')
    stop = Handler('stop', '/stop')
    help = Handler('help', '/help')


class Commands:
    learn = 'Учить'
    miss = 'Пропустить'
