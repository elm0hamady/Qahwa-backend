from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import Topic,Question


@receiver([post_save, post_delete], sender=Question)
@receiver([post_delete], sender=Topic)
def invalidate_topic_cache(sender, instance, **kwargs):
    print("Clearing topic cache")
    cache.delete_pattern("*topic_list*")