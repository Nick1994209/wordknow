from django.http import HttpResponseRedirect
from django.urls import reverse

from app.models import User


class SetCookiesMixin:
    def __init__(self, *args, **kwargs):
        self._response_cookies = {}
        super().__init__(*args, **kwargs)

    def set_cookies(self, key, value):
        self._response_cookies[key] = value

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)

        if self._response_cookies:
            for k, v in self._response_cookies.items():
                response.set_cookie(k, v)
        return response

    def form_valid(self, form):
        response = super().form_valid(form)
        if self._response_cookies:
            for k, v in self._response_cookies.items():
                response.set_cookie(k, v)
        return response


class AuthenticationMixin(SetCookiesMixin):
    auth_cookie_name = 'wordknow_auth'
    auth_required = False
    auth_redirect_url = 'index'

    def __init__(self, *args, **kwargs):
        self._user = None
        super().__init__(*args, **kwargs)

    def identification(self, request):
        # получаем пользователя по куке

        auth_token = request.COOKIES.get(self.auth_cookie_name)
        if not auth_token:
            self._user = None
            return
        self._user = User.objects.filter(auth_token=auth_token).first()

    def authenticate(self, user: User, auth_code: str):
        # устанавливаем пользовательский токен в куку

        if user.auth_code != auth_code:
            return False

        user.generate_auth_token()
        self.set_cookies(self.auth_cookie_name, str(user.auth_token))
        return True

    def get_context_data(self, **context_data):
        context_data = super().get_context_data(**context_data)
        context_data['user'] = self._user
        return context_data

    def dispatch(self, request, *args, **kwargs):
        self.identification(request)

        # если пользоавтель не авторизован и view требует авторизации, то редиректим пользователя
        if self.auth_required and not self._user:
            return HttpResponseRedirect(self.get_auth_redirect_url())

        return super().dispatch(request, *args, **kwargs)

    def get_auth_redirect_url(self):
        return reverse(self.auth_redirect_url)


class TemplateFormMixin:
    template_name = 'app/form.html'
    title = None
    button_name = 'Отправить'

    def get_context_data(self, **context_data):
        context = super().get_context_data(**context_data)
        context['title'] = self.title
        context['button_name'] = self.button_name
        return context

    def render_form(self, form, errors=None):
        return self.render_to_response(self.get_context_data(form=form, errors=errors))
