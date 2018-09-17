from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView, FormView, ListView, CreateView
from django import forms as django_forms

from app.mixins import AuthenticationMixin, TemplateFormMixin
from app.models import User, Word
from app import forms
from telegram.tasks import safe_send_message


class IndexView(AuthenticationMixin, TemplateView):
    template_name = 'app/index.html'


class LoginView(AuthenticationMixin, TemplateFormMixin, FormView):
    form_class = forms.LoginForm
    success_url = 'words'
    button_name = 'Вход'

    def get_form_kwargs(self, hide_auth_code=False):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'GET' or hide_auth_code:
            kwargs['hide_auth_code'] = True
        return kwargs

    def form_valid(self, form):
        form.fields['auth_code'].required = True
        form.fields['user'].widget.attrs['readonly'] = True

        if not form.has_auth_token():
            return self.send_password_and_show_form(form)

        return self.try_authenticate(form)

    def send_password_and_show_form(self, form):

        user = form.cleaned_data['user']
        user.generate_auth_code()
        msg = 'Для получения доступа к личному кабинету введите пароль: %s' % user.auth_code

        if safe_send_message(user, msg):
            return self.render_form(form)
        else:
            form = self.form_class(**self.get_form_kwargs(hide_auth_code=True))
            return self.render_form(
                form, errors='Не смог отправить сообщение в telegram. Попробуйте еще раз.',
            )

    def try_authenticate(self, form):
        if not self.authenticate(form.cleaned_data['user'], form.cleaned_data['auth_code']):
            return self.render_form(form, errors='Пароли не совпадают.')
        return super().form_valid(form)


class WordView(AuthenticationMixin, ListView):
    model = Word
    template_name = 'app/words.html'
    ordering = '-id'

    def get_queryset(self):
        qs = super().get_queryset()
        if self._user:
            return qs.filter(user=self._user)
        return qs.filter(user=None)


class CreateWordsView(AuthenticationMixin, TemplateFormMixin, FormView):
    button_name = 'Добавить слова'
    auth_required = True
    success_url = 'words'
    form_class = forms.WordsForm
    initial = {'splitter': ';', 'first_run': True}

    def form_valid(self, form):
        if form.is_first_run():
            return self.render_show_user_words(form)
        else:
            self.save_words(form)
            return super().form_valid(form)

    def render_show_user_words(self, form):
        form = self.form_class({
            **form.cleaned_data,
            'first_run': False,
            'words': form.get_without_trash_words(),
        })
        form.set_readonly()
        return self.render_to_response(self.get_context_data(form=form))

    def save_words(self, form: forms.WordsForm):
        words = [Word(text=text, translate=translate, user=self._user)
                 for text, translate in form.get_translates()]
        Word.objects.bulk_create(words, batch_size=500)
