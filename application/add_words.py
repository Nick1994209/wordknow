def set_django_env():
    import sys, os
    import django

    module, _ = os.path.split(__file__)
    sys.path.append(module)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
    django.setup()


set_django_env()

from app.models import Word

print(Word.objects.all())
with open('words', 'r', encoding='utf-8') as f:
    file_data = f.read()
file_data = file_data.replace('\t\t', '\t')
for row in file_data.split('\n'):
    if not row:
        continue
    row.replace('\n', '')
    r = row.split('\t')
    if len(r) >= 2:
        text, translate = r[0], r[-1]
        print(text.capitalize(), translate.capitalize())
        Word.objects.create(text=text.capitalize(), translate=translate.capitalize())
