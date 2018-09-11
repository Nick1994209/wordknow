def set_django_env():
    import sys, os
    import django

    module, _ = os.path.split(__file__)
    sys.path.append(module)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
    django.setup()


def set_words(file_path, split):
    from app.models import Word

    with open(file_path, 'r', encoding='utf-8') as f:
        file_data = f.read()

    count_added_words = 0
    for row in file_data.split('\n'):
        if not row:
            continue

        r = row.split(split)

        if len(r) >= 2:
            text, translate = r[0], r[-1]
            print(text.capitalize(), translate.capitalize())
            Word.objects.create(text=text.capitalize(), translate=translate.capitalize())
            count_added_words += 1

    print('count_added_words', count_added_words)


if __name__ == '__main__':
    set_django_env()
    set_words('dictionary.txt', split=';')
