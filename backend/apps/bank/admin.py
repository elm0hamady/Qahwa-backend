from django.contrib import admin
from .models import Category, Topic, Question, Answer, Media


admin.site.register(Answer)
admin.site.register(Media)

class AnswerInline(admin.StackedInline):
    model = Answer
    extra = 1

class MediaInline(admin.StackedInline):
    model = Media
    extra = 1

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text','topic','difficulity']
    list_filter = ['difficulity','topic']
    search_fields = ['text']
    inlines = [ AnswerInline,MediaInline ]

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name','category']
    list_filter = ['category']
    search_fields = ['name']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
