from django.urls import path
from app import views


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('login', views.LoginView.as_view(), name='login'),
    path('words', views.WordView.as_view(), name='words'),
    path('create_word', views.CreateWordsView.as_view(), name='create_words'),
]
