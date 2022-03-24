from django.dispatch import receiver
from django.db.models.signals import post_save


from .tasks import post_save_post, notify_managers_posts


def create_post():
    post_save_post.delay()
    notify_managers_posts.delay()



# # так тоже не работает!
# @receiver(post_save)
# def signals(**kwargs):
#     post_save_post()
#     notify_managers_posts()
