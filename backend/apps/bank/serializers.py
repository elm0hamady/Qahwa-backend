from rest_framework import serializers
from apps.bank.models import Topic


class TopicSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name')
    class Meta:
        model = Topic
        fields = ['id','category','name']