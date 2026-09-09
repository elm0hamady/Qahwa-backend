from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework import generics 
from rest_framework.permissions import IsAuthenticated,AllowAny
from .models import Topic
from .services import get_ready_topics
from .serializers import TopicSerializer

class TopicListView(generics.ListAPIView):
    serializer_class = TopicSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category']
    search_fields = ['name']

    @method_decorator(cache_page(60*60*3,key_prefix='topic_list'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        ready_topic_ids = [t.id for t in get_ready_topics()]
        return Topic.objects.filter(id__in=ready_topic_ids).order_by('category', 'name')