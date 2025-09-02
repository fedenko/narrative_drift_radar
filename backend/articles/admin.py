from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published_date', 'created_at')
    list_filter = ('source', 'published_date')
    search_fields = ('title', 'content')
    readonly_fields = ('embedding', 'created_at', 'updated_at')
