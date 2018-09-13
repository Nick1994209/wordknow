from argparse import ArgumentParser


def set_django_env():
    import sys, os
    import django

    module, _ = os.path.split(__file__)
    sys.path.append(module)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
    django.setup()


def get_words(file_path, split):
    with open(file_path, 'r', encoding='utf-8') as f:
        file_data = f.read()

    for row in file_data.split('\n'):
        if not row:
            continue

        r = row.split(split)

        if len(r) >= 2:
            text, translate = r[0], r[-1]
            yield text, translate


def set_words(file_path, split, user=None):
    from app.models import Word

    count_words = 0
    for text, translate in get_words(file_path, split):
        Word.objects.create(text=text.capitalize(), translate=translate.capitalize(), user_id=user)
        count_words += 1

    print('count_added_words', count_words)


def args_parser():

    parser = ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('-f', '--file_path')
    parser.add_argument('-u', '--user')
    parser.add_argument('-s', '--split')

    parsed_args = parser.parse_args()
    args = {}

    for arg_name in ['file_path', 'user', 'split']:
        if getattr(parsed_args, arg_name):
            args[arg_name] = getattr(parsed_args, arg_name)

    return args


def a(**kwargs):
    print(kwargs)


if __name__ == '__main__':
    set_django_env()
    default = dict(split=';')

    # python application/manage.py migrate --user 2 --file_path words/nicking.txt
    set_words(**default, **args_parser())
