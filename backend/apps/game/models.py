import uuid
from django.db import models
from django.db.models import Q
from django.conf import settings
from apps.bank.models import Question,Topic

class Session(models.Model):
    class SessionStatus(models.TextChoices):
        INPROGRESS = 'in_progress'
        FINISHED = 'finished'

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    host = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    status = models.CharField(max_length=15,default=SessionStatus.INPROGRESS,choices=SessionStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'game_session'
        constraints = [
            models.UniqueConstraint(
                fields=['host'],
                condition=Q(status='in_progress'),
                name='one_active_session_per_host'
            )]

    def __str__(self):
        return f'Session of {self.host.username}'


class SessionTopic(models.Model):

    session = models.ForeignKey(Session,on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic,on_delete=models.PROTECT)

    class Meta:
        db_table = 'game_sessiontopic'
        constraints = [
            models.UniqueConstraint(
                    fields=['session','topic'],
                    name='cant_pick_same_topic_in_same_session'
        )]

    def __str__(self):
        return f'Topic {self.topic.name} of session {self.session.pk}'


class Player(models.Model):

    name = models.CharField(max_length=25)
    session = models.ForeignKey(Session,on_delete=models.CASCADE)
    manual_adjustment = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'game_player'

    def __str__(self):
        return self.name


class SessionQuestion(models.Model):
    class QuestionState(models.TextChoices):
        LOCKED = 'locked'
        OPENED = 'opened'
        JUDGED = 'judged'

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    session = models.ForeignKey(Session,on_delete=models.CASCADE)
    question = models.ForeignKey(Question,on_delete=models.PROTECT)
    assigned_player = models.ForeignKey(Player,on_delete=models.PROTECT,related_name='assigned_questions')
    winner_player = models.ForeignKey(Player,on_delete=models.PROTECT,null=True,blank=True,related_name='won_questions')
    state = models.CharField(max_length=10, choices=QuestionState.choices, default=QuestionState.LOCKED)
    opened_at = models.DateTimeField(null=True, blank=True)
    judged_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
            db_table = 'game_sessionquestion'
            constraints = [
                models.UniqueConstraint(
                        fields=['session','question','assigned_player'],
                        name='question_unique_per_session_and_player'
            )]
    
    def __str__(self):
        return f'Topic {self.question.text[:30]} of session {self.session.pk}'



