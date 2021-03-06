from collections import namedtuple


class Handlers:
    Handler = namedtuple('Handler', ('handler', 'path'))
    learn_words = Handler('learn_words', '/learn_words')
    repetition = Handler('repetition', '/repetition')
    stop_learning_word = Handler('stop_learning_word', '/stop_learning_word')
    stop = Handler('stop', '/stop')
    help = Handler('help', '/help')


class Commands:
    learn = 'Учить'
    miss = 'Пропустить'


class Emogies:
    astronaut = '\U0001F680'  # ':man_astronaut:'
    rocket = '\U0001F680'  # ':rocket:'
    astonished = '\U0001F632'  # ':astonished:'
    wink = '\U0001F609'  # ':wink:'  # подмигивание
    fearful = '\U0001F628'  # ':fearful:'
    headphones = '🎧'
    picture = '🖼'
