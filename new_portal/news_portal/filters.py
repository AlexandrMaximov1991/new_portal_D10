from django_filters import FilterSet
from .models import *


class News_filter(FilterSet):

    class Meta:
        model = Post
        fields = {'postTitle': ['icontains'],
                  'pubData': ['gt'],
                  'PostAuthor': ['in']}
