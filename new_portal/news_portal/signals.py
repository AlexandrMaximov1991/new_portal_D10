from django.dispatch import receiver
from django.db.models.signals import post_save, m2m_changed
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string

from django.db.models.signals import post_save
from .models import Post, Category

from .tasks import post_save_post, notify_managers_posts
from .views import *


@receiver(post_save)
def create_post():
    post_save_post()
    notify_managers_posts()



# # при сохранении объекта модели Пост будет срабатывать этот сигнал
# @receiver(post_save, sender=Post)
# def post_save_post(created, **kwargs):  # получить параметры можно двумя способами. Первый тут
#     # А можно вытащить из kwargs
#     # тут вытаскиваем объект только что сохранённого поста
#     post_instance = kwargs['instance']
#
#     # собираем почту всех, кто подписался на категории этой статьи
#     # множество тут у меня для того, чтобы не было повторений, чтобы несколько раз не приходило одно и то же письмо
#     # но на этапе формирования письма надо будет передать именно список
#     subscribers_list = {user.email
#                         for category in post_instance.postCategory.all()
#                         for user in category.subscribers.all()}
#     email_from = settings.DEFAULT_FROM_EMAIL
#
#     # если статья создана
#     if created:
#         # отправка письма с превью и ссылкой на статью
#         subject = 'В категориях, на которые вы подписаны появилась новая статья'
#         text_message = f'В категориях, на которые вы подписаны появилась новая статья:'
#     else:
#         # отправка письма с ссылкой на статью и помекой об изменении
#         subject = 'Произошли изменения в публикации!'
#         text_message = f'В публикации произошли изменения! Они доступны  '
#
#     # рендерим в строку шаблон письма и передаём туда переменные, которые в нём используем
#     render_html_template = render_to_string('send.html', {'post': post_instance, 'subject': subject, 'text_message': text_message})
#
#     # формируем письмо
#     msg = EmailMultiAlternatives(subject, text_message, email_from, list(subscribers_list))
#     # прикрепляем хтмл-шаблон
#     msg.attach_alternative(render_html_template, 'text/html')
#     # отправляем
#     msg.send()
#
#
# @receiver(m2m_changed, sender=Post.postCategory.through)
# def notify_managers_posts(instance, action, pk_set, *args, **kwargs):
#     if action == 'post_add':
#         html_content = render_to_string(
#             'mail_create.html',
#             {'post': instance,
#              }
#         )
#         for pk in pk_set:
#             category = Category.objects.get(pk=pk)
#             recipients = [user.email for user in category.subscribers.all()]
#             msg = EmailMultiAlternatives(
#                 subject=f'На сайте NewsPaper новая статья: {instance.postTitle}',
#
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 to=recipients
#             )
#             msg.attach_alternative(html_content, "text/html",)
#             msg.send()
