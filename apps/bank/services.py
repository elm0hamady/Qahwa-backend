from django.db.models import Count
from core.constants import DIFFICULTIES, MIN_QUESTIONS_PER_DIFFICULTY
from apps.bank.models import Question, Topic

def get_ready_topics():
    ready_topics = []
    
    counts = (
        Question.objects
        .all()
        .values("topic_id","difficulity")
        .annotate(count=Count("id"))
    )
    counts_by_topic_and_difficulty = {
            (row["topic_id"], row["difficulity"]): row["count"] for row in counts
        }
    for topic in Topic.objects.all():
        is_ready = all(
            counts_by_topic_and_difficulty.get((topic.id, difficulty), 0) >= MIN_QUESTIONS_PER_DIFFICULTY
            for difficulty in DIFFICULTIES
        )
        
        if is_ready:
            ready_topics.append(topic)

    return ready_topics