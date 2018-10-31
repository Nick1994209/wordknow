from django.urls import path

from app import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('about_bot', views.AboutBotView.as_view(), name='about_bot'),
    path('enter_login', views.EnterLoginView.as_view(), name='enter_login'),
    path('login', views.LoginView.as_view(), name='login'),
    path('words', views.WordView.as_view(), name='words'),
    path('create_word', views.CreateWordsView.as_view(), name='create_words'),
]
