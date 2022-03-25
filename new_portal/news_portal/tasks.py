from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
import logging
from .models import Post, Category


from celery import shared_task
import datetime

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from collections import defaultdict

from ..new_portal import settings

logger = logging.getLogger(__name__)


def send_posts(email_list, posts):
    # на случай, если там только один адрес, а не список
    if isinstance(email_list, str):
        subscriber_list = [email_list, ]
    else:
        subscriber_list = email_list

    email_form = settings.DEFAULT_FROM_EMAIL
    subject = 'В категориях, на которые вы подписаны появились новые статьи'
    text_message = 'В категориях, на которые вы подписаны появились новые статьи'

    # рендерим в строку шаблон письма и передаём туда переменные, которые в нём используем
    render_html_template = render_to_string('send_posts_list.html', {'posts': posts, 'subject': subject})

    # формируем письмо
    msg = EmailMultiAlternatives(subject, text_message, email_form, list(subscriber_list))

    # прикрепляем html-шаблон
    msg.attach_alternative(render_html_template, 'text/html')
    # отправляем
    msg.send()


@shared_task
def email_weekly():
    print('Start email_weekly')
    today = datetime.datetime.now()
    last_week = today - datetime.timedelta(days=7)
    last_week_posts_qs = Post.objects.filter(pubData__gte=last_week)

    # собираем в словарь список пользователей и список постов, которые им надо разослать
    posts_for_user = defaultdict(set)  # user -> posts

    for post in last_week_posts_qs:
        for category in post.postCategory.all():
            for user in category.subscribers.all():
                posts_for_user[user].add(post)

    # непосредственно рассылка
    for user, posts in posts_for_user.items():
        send_posts(user.email, posts)

        print('Finish')


@shared_task
def post_save_post(created, **kwargs):  # получить параметры можно двумя способами. Первый тут
    # А можно вытащить из kwargs
    # тут вытаскиваем объект только что сохранённого поста
    post_instance = kwargs['instance']

    # собираем почту всех, кто подписался на категории этой статьи
    # множество тут у меня для того, чтобы не было повторений, чтобы несколько раз не приходило одно и то же письмо
    # но на этапе формирования письма надо будет передать именно список
    subscribers_list = {user.email
                        for category in post_instance.postCategory.all()
                        for user in category.subscribers.all()}
    email_from = settings.DEFAULT_FROM_EMAIL

    # если статья создана
    if created:
        # отправка письма с превью и ссылкой на статью
        subject = 'В категориях, на которые вы подписаны появилась новая статья'
        text_message = f'В категориях, на которые вы подписаны появилась новая статья:'
    else:
        # отправка письма с ссылкой на статью и помекой об изменении
        subject = 'Произошли изменения в публикации!'
        text_message = f'В публикации произошли изменения! Они доступны  '


    # рендерим в строку шаблон письма и передаём туда переменные, которые в нём используем
    render_html_template = render_to_string('send.html', {'post': post_instance, 'subject': subject, 'text_message': text_message})

    # формируем письмо
    msg = EmailMultiAlternatives(subject, text_message, email_from, list(subscribers_list))
    # прикрепляем хтмл-шаблон
    msg.attach_alternative(render_html_template, 'text/html')
    # отправляем
    msg.send()
    post_save(post_save_post, sender=Post)


@shared_task
def notify_managers_posts(instance, action, pk_set, *args, **kwargs):
    if action == 'post_add':
        html_content = render_to_string(
            'mail_create.html',
            {'post': instance,
             }
        )
        for pk in pk_set:
            category = Category.objects.get(pk=pk)
            recipients = [user.email for user in category.subscribers.all()]
            msg = EmailMultiAlternatives(
                subject=f'На сайте NewsPaper новая статья: {instance.postTitle}',

                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients
            )
            msg.attach_alternative(html_content, "text/html",)
            msg.send()


    post_save(notify_managers_posts, sender=Post.postCategory.through)
