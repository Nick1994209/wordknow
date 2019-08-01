from django import forms

from app.models import User


class EnterLoginForm(forms.Form):
    user = forms.CharField(label='Telegram username', max_length=200)

    def clean_user(self) -> User:
        try:
            return User.objects.get(username=self.cleaned_data['user'])
        except User.DoesNotExist:
            raise forms.ValidationError('Пользователь не найден')


class LoginForm(EnterLoginForm):
    user = forms.CharField(label='Telegram username', max_length=200, disabled=True)
    auth_code = forms.CharField(
        label='Пароль', help_text='Должен прийти в telegram',
        widget=forms.PasswordInput(), max_length=4,
    )


class WordsForm(forms.Form):
    words = forms.CharField(
        label='Слова', widget=forms.Textarea(), max_length=150000, required=False,
        help_text='Добавляйте слова разделяя слово с переводом знаком разделения. '
                  'С переносом строки можно добавить еще слова с переводом. Пример: "hello;привет"')
    splitter = forms.CharField(label='Знак разделения слова с переводом')
    first_run = forms.NullBooleanField(widget=forms.HiddenInput())

    def get_without_trash_words(self):
        splitter = self.cleaned_data['splitter']
        splitter = splitter.replace('\\t', '\t')
        lines = [
            '{text}{splitter}{translate}'.format(text=text, splitter=splitter, translate=translate)
            for text, translate in self.get_translates()
        ]
        return '\n'.join(lines)

    def get_translates(self):
        translates = []
        splitter = self.cleaned_data['splitter']
        for line in self.cleaned_data['words'].splitlines():
            split_line = line.split(splitter)
            if len(split_line) != 2:
                continue

            text, translate = split_line
            translates.append((text.strip(), translate.strip()))

        return translates

    def is_first_run(self):
        return self.cleaned_data['first_run'] is True

    def set_readonly(self):
        for _, field in self.fields.items():
            field.widget.attrs['readonly'] = True
