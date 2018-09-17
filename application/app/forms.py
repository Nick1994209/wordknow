from django import forms
from app.models import User


class LoginForm(forms.Form):
    user = forms.CharField(label='Telegram username', max_length=200)
    auth_code = forms.CharField(
        label='Пароль', help_text='Должен прийти в telegram',
        widget=forms.PasswordInput(), max_length=4, required=False,
    )

    def __init__(self, *args, **kwargs):
        hide_auth_code = kwargs.pop('hide_auth_code', False)
        super().__init__(*args, **kwargs)
        if hide_auth_code:
            self.fields.pop('auth_code')

    def clean_user(self) -> User:
        try:
            return User.objects.get(username=self.cleaned_data['user'])
        except User.DoesNotExist:
            raise forms.ValidationError('Пользователь не найден')

    def has_auth_token(self):
        return bool(self.cleaned_data['auth_code'])


class WordsForm(forms.Form):
    words = forms.CharField(label='Слова', widget=forms.Textarea(), max_length=10000,
                            required=False)
    splitter = forms.CharField(label='Знак разделения слов')
    first_run = forms.NullBooleanField(widget=forms.HiddenInput())

    def get_without_trash_words(self):
        splitter = self.cleaned_data['splitter']
        lines = [f'{text}{splitter}{translate}' for text, translate in self.get_translates()]
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
        return self.cleaned_data['first_run'] == True

    def set_readonly(self):
        for _, field in self.fields.items():
            field.widget.attrs['readonly'] = True
