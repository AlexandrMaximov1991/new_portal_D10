from django import template

register = template.Library()

CENSOR = ['пропустит', 'массово', 'заражения']


@register.filter(name='censor')
def censor(value):
    text = value.split()
    for word in text:
        if word.lower() in CENSOR:
            value = value.replace(word, '*' * len(word))
    return value
