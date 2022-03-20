from django.forms import ModelForm, DateTimeField
from .models import *


# Создаём модельную форму
class PostForm(ModelForm):
    # pubData = DateTimeField()
    class Meta:
        model = Post
        fields = ['postTitle', 'postText', 'postCategory', 'PostAuthor']