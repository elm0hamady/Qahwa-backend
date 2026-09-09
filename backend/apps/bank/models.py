import os
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError

class Category(models.Model):

    name = models.CharField(max_length=50,unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bank_category'

    def __str__(self):
        return self.name
    

class Topic(models.Model):

    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category,on_delete=models.PROTECT)

    class Meta:
        db_table = 'bank_topic'
        constraints =[
            models.UniqueConstraint(
                    fields=['name','category'],
                    name='unique_name_per_category'
            )]

    def __str__(self):
        return self.name
    

class Question(models.Model):
    class QuestionDiffculity(models.IntegerChoices):
        EASY = 100, 'Easy'
        MEDIUM = 300, 'Medium'
        HARD = 500, 'Hard'

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    topic = models.ForeignKey(Topic,on_delete=models.PROTECT)
    difficulity = models.IntegerField(choices=QuestionDiffculity.choices)

    class Meta:
        db_table = 'bank_question'  
        indexes = [
            models.Index(fields=['topic', 'difficulity'], name='idx_question_topic_difficulty')
        ]

    def __str__(self):
        return self.text[:50]


class Answer(models.Model):

    text = models.TextField()
    question = models.OneToOneField(Question,on_delete=models.CASCADE)

    class Meta:
        db_table = 'bank_answer'

    def __str__(self):
        return self.text[:50]
    

class Media(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = 'image'
        VIDEO = 'video'
        AUDIO = 'audio' 

    file = models.FileField(upload_to='files/%y/%m/%d')
    question = models.OneToOneField(Question,on_delete=models.CASCADE,null=True,blank=True)
    media_type = models.CharField(max_length=10,choices=MediaType.choices)
    answer = models.OneToOneField(Answer,on_delete=models.CASCADE,null=True,blank=True)

    class Meta:
        db_table = 'bank_media'
        constraints =[
            models.CheckConstraint(
                    name='prevent_null_question_answer_or_filled_both_at_same_time',
                    condition=(Q(answer__isnull=True , question__isnull=False) |
                                Q(answer__isnull=False , question__isnull=True))
            )]
    
    def __str__(self):
        owner = self.question or self.answer
        return f'{self.media_type} for {owner.text[:30]}'

    def clean(self):
        IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
        AUDIO_EXTENSIONS = ['.mp3', '.wav']
        VIDEO_EXTENSIONS = ['.mp4', '.webm']

        MAX_SIZES = {
            'image': 3 * 1024 * 1024,   # 3 MB بالبايت
            'audio': 7 * 1024 * 1024,   # 7 MB
            'video': 35 * 1024 * 1024,  # 35 MB
        }

        EXTENSIONS_MAP = {
            'image': IMAGE_EXTENSIONS,
            'audio': AUDIO_EXTENSIONS,
            'video': VIDEO_EXTENSIONS,
        }

        extension = os.path.splitext(self.file.name)[1].lower()
        size = self.file.size

        if extension not in  EXTENSIONS_MAP[self.media_type]:
            raise ValidationError(f'{self.media_type} should be {EXTENSIONS_MAP[self.media_type]} extension.')
            
        if size > MAX_SIZES[self.media_type]:
            raise ValidationError(f'Maximum size should be less than {MAX_SIZES[self.media_type]}.')
        return super().clean()