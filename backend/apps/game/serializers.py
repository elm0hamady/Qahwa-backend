from rest_framework import serializers
from apps.game.models import Player,Session,SessionTopic,SessionQuestion


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['id','name']

class SessionTopicSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='topic.id')
    name = serializers.CharField(source='topic.name')
    class Meta:
        model = SessionTopic
        fields = ['id','name']

class SessionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='public_id', read_only=True)
    players = PlayerSerializer(source='player_set', many=True, read_only=True)
    topics = SessionTopicSerializer(source='sessiontopic_set', many=True, read_only=True)
    class Meta:
        model = Session
        fields = ['id','status','created_at','topics','players']

class SessionQuestionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='public_id',read_only=True)
    topic = serializers.CharField(source='question.topic.name')
    difficulity = serializers.IntegerField(source='question.difficulity')
    player = serializers.CharField(source = 'assigned_player.name')
    player_id = serializers.IntegerField(source='assigned_player_id')
    text = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()

    def get_text(self, obj):
        if obj.state == SessionQuestion.QuestionState.LOCKED:
            return None
        return obj.question.text

    def get_media(self, obj):
        if obj.state == SessionQuestion.QuestionState.LOCKED:
            return None
        if not hasattr(obj.question, 'media'):
            return None
        return {
            'type': obj.question.media.media_type,
            'url': obj.question.media.file.url
        }

    class Meta:
        model = SessionQuestion
        fields = ['id','topic','difficulity','player','state','text','media','player_id']

class ScoreboardEntrySerializer(serializers.Serializer):
    player_id = serializers.IntegerField()
    player_name = serializers.CharField()
    score = serializers.IntegerField()

class StartSessionInputSerializer(serializers.Serializer):
    player1_name = serializers.CharField(max_length=100)
    player2_name = serializers.CharField(max_length=100)
    topic_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=4,
        max_length=4
    )

class JudgeQuestionInputSerializer(serializers.Serializer):
    winner_player_id = serializers.IntegerField(required=False, allow_null=True)

class AdjustScoreInputSerializer(serializers.Serializer):
    amount = serializers.IntegerField()