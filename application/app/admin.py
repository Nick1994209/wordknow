from django.contrib import admin

from .models import LearningStatus, User, Word, WordStatus

admin.site.register(User)


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_created'
    search_fields = ('text', 'translate', 'user__username', 'date_created')
    filter_fields = ('date_created', 'user')
    list_display = ('__str__', 'user', 'date_created', 'date_updated',)


@admin.register(WordStatus)
class WordStatusAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_created'
    search_fields = ('user__username', 'word__text', 'word__translate')
    filter_fields = ('user', )
    list_display = ('__str__',  'user', 'date_created', 'date_updated',)


@admin.register(LearningStatus)
class LearningStatusAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_created'
    search_fields = ('user__username', 'word__text', 'word__translate')
    filter_fields = ('user',)
    list_display = ('__str__',  'user', 'date_created', 'date_updated',)
