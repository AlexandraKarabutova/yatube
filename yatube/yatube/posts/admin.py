from django.contrib import admin

from .models import Comment, Follow, Group, Post


class CommentInline(admin.TabularInline):
    model = Comment


class PostAdmin(admin.ModelAdmin):
    inlines = [CommentInline]
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class PostGroup(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('pk', 'title', 'slug')
    search_fields = ('title',)
    list_filter = ('title',)
    empty_value_display = '-пусто-'


class FollowAdmin(admin.ModelAdmin):
    model = Follow


admin.site.register(Post, PostAdmin)
admin.site.register(Group, PostGroup)
admin.site.register(Follow, FollowAdmin)
admin.site.register(Comment)
