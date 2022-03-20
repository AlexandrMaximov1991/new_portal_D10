from django.contrib import admin
from .models import Author, Category, Post, PostCategory


admin.site.register(Author)
admin.site.register(Category)
admin.site.register(Post)
