from django.contrib import admin

from .models import LearningStatus, User, Word, WordStatus

admin.site.register(User)
admin.site.register(Word)
admin.site.register(WordStatus)
admin.site.register(LearningStatus)
