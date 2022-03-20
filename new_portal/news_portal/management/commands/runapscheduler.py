import logging
from _multiprocessing import send

from collections import defaultdict
import datetime

from django.template.loader import render_to_string
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution

from news_portal.models import Post

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


# наша задача по выводу текста на экран
def send_posts_to_email_weekly():
    """
    таск который выбирает все посты, опубликованные за неделю и рассылающий
    (через вызов вспомогательной функции) их всем, кто подписан на категории, куда эти статьи входят
    :return: None
    """
    # берём посты за последние 7 дней
    # здесь мы получаем queryset
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


# функция, которая будет удалять неактуальные задачи
def delete_old_job_executions(max_age=604_800):
    """This job deletes all apscheduler job executions older than `max_age` from the database."""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs apscheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # добавляем работу нашему задачнику
        scheduler.add_job(
            send_posts_to_email_weekly,
            trigger=CronTrigger(
                day_of_week="mon",
                hour="09",
                minute="00"
            ),
            # То же, что и интервал, но задача тригера таким образом более понятна django
            id="send_posts_to_email_weekly",  # уникальный айди
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'send_posts_to_email_weekly'.")

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="mon", hour="00", minute="00"
            ),
            # Каждую неделю будут удаляться старые задачи, которые либо не удалось выполнить, либо уже выполнять не надо.
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info(
            "Added weekly job: 'delete_old_job_executions'."
        )

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")
