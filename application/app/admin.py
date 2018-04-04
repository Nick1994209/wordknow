from django.contrib import admin

from .models import LearningStatus, User, Word, WordStatus

admin.site.register(User)
admin.site.register(LearningStatus)


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_created'
    search_fields = ('text', 'translate', 'date_created')
    filter_fields = ('date_created', )
    list_display = ('__str__', 'date_created')


@admin.register(WordStatus)
class WordStatusAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_created'
    search_fields = ('user__username', 'word__text', 'word__translate')
    list_display = ('__str__', 'date_created', 'user')
