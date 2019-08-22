from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseRedirect
from django.views.generic import FormView, ListView, TemplateView

from app import forms
from app.mixins import AuthenticationMixin, TemplateFormMixin
from app.models import Word
from telegram.utils import safe_send_message


class IndexView(AuthenticationMixin, TemplateView):
    template_name = 'app/index.html'
    extra_context = {'bot_name': settings.TELEGRAM_BOT_NAME}


class SchedulerView(AuthenticationMixin, TemplateView):
    template_name = 'app/scheduler.html'
    extra_context = {'bot_name': settings.TELEGRAM_BOT_NAME,
                     'repetition_times': settings.REPETITION_TIMES}


class EnterLoginView(AuthenticationMixin, TemplateFormMixin, FormView):
    form_class = forms.EnterLoginForm
    success_url = 'login'
    button_name = 'Войти'
    title = 'Вход'

    def form_valid(self, form):
        user = form.cleaned_data['user']
        user.generate_auth_code()
        msg = 'Для получения доступа к личному кабинету введите пароль: %s' % user.auth_code

        if safe_send_message(user, msg):
            params = urlencode({'user': user.username})
            url = '{}?{}'.format(self.get_success_url(), params)
            return HttpResponseRedirect(url)
        else:
            return self.render_form(
                form, errors='Не смог отправить сообщение в telegram. Попробуйте еще раз.',
            )


class LoginView(AuthenticationMixin, TemplateFormMixin, FormView):
    form_class = forms.LoginForm
    success_url = 'words'
    title = 'Вход'
    button_name = 'Вход'

    def get_initial(self):
        return {'user': self.request.GET.get('user', '')}

    def form_valid(self, form):
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
        words = [Word(text=text, translate=translate, phrase=phrase, user=self._user)
                 for text, translate, phrase in form.get_translates()]
        Word.objects.bulk_create(words, batch_size=500)
