import random
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count ,Sum
from apps.game.models import Session, Player, SessionTopic, SessionQuestion
from apps.bank.models import Question,Answer
from core.constants import DIFFICULTIES, MIN_QUESTIONS_PER_DIFFICULTY,REQUIRED_TOPIC_COUNT
from core.exceptions import (
    QuestionNotOpenedError,
    SessionAlreadyActiveError,
    InvalidTopicCountError,
    DuplicateTopicError,
    InsufficientQuestionPoolError,
    QuestionAlreadyOpenedError,
    QuestionAlreadyJudgedError,
    PlayerNotInSessionError,
    InvalidAdjustmentAmountError,
    NoActiveSessionError,
)


def validate_start_session(host, topic_ids):
    """كل عمليات التحقق قبل أي إنشاء فعلي في الداتابيز"""

    if Session.objects.filter(host=host, status=Session.SessionStatus.INPROGRESS).exists():
        raise SessionAlreadyActiveError("Host already has an active session.")

    if len(topic_ids) != REQUIRED_TOPIC_COUNT:
        raise InvalidTopicCountError(f"Exactly {REQUIRED_TOPIC_COUNT} topics required.")

    if len(set(topic_ids)) != len(topic_ids):
        raise DuplicateTopicError("Duplicate topics are not allowed.")

    
    counts = (
    Question.objects
    .filter(topic_id__in=topic_ids)
    .values("topic_id", "difficulity")
    .annotate(count=Count("id"))
)
    counts_by_topic_and_difficulty = {
        (row["topic_id"], row["difficulity"]): row["count"] for row in counts
    }

    for topic_id in topic_ids:
        for difficulty in DIFFICULTIES:
            available = counts_by_topic_and_difficulty.get((topic_id, difficulty), 0)
            if available < MIN_QUESTIONS_PER_DIFFICULTY:
                raise InsufficientQuestionPoolError(
                    f"Topic {topic_id} has only {available} questions at difficulty {difficulty}, "
                    f"minimum {MIN_QUESTIONS_PER_DIFFICULTY} required."
                )

def start_session(host, player1_name, player2_name, topic_ids):
    validate_start_session(host=host,topic_ids=topic_ids)
    session_questions = []
    
    with transaction.atomic():
        session = Session.objects.create(host=host)
        player1_obj = Player.objects.create(name=player1_name, session=session)
        player2_obj = Player.objects.create(name=player2_name, session=session)

        for topic_id in topic_ids:
            SessionTopic.objects.create(session=session, topic_id=topic_id)

        for topic_id in topic_ids:
            for difficulity in DIFFICULTIES:
                available_questions = list(
                    Question.objects.filter(topic_id=topic_id, difficulity=difficulity)
                )
                chosen_two = random.sample(available_questions, 2)
                session_questions.append(
                    SessionQuestion(session=session, question=chosen_two[0], assigned_player=player1_obj)
                )
                session_questions.append(
                    SessionQuestion(session=session, question=chosen_two[1], assigned_player=player2_obj)
                )

        SessionQuestion.objects.bulk_create(session_questions)
    
    return session

def open_question(session_question_id):
    session_question = SessionQuestion.objects.get(id=session_question_id)
    if session_question.state == SessionQuestion.QuestionState.LOCKED:
        session_question.state = SessionQuestion.QuestionState.OPENED
        session_question.opened_at = timezone.now()
        session_question.save()
    else:
        raise QuestionAlreadyOpenedError()
    return session_question

def finish_session(session):
    session.status = Session.SessionStatus.FINISHED
    session.save()
    return None

def judge_question(session_question_id, winner_player_id=None):
    session_question = SessionQuestion.objects.get(id=session_question_id)

    if session_question.state != SessionQuestion.QuestionState.OPENED:
        raise QuestionAlreadyJudgedError()

    winner_player = None
    if winner_player_id is not None:
        winner_player = Player.objects.get(id=winner_player_id)
        if winner_player.session_id != session_question.session_id:
            raise PlayerNotInSessionError()

    session_question.winner_player = winner_player
    session_question.state = SessionQuestion.QuestionState.JUDGED
    session_question.judged_at = timezone.now()
    session_question.save()
    if not SessionQuestion.objects.filter(session=session_question.session).exclude(state=SessionQuestion.QuestionState.JUDGED).exists():
        finish_session(session_question.session)
    return session_question

def get_scoreboard(session):
    scoreboard = {}
    for player in session.player_set.all():
        result = player.won_questions.aggregate(total=Sum('question__difficulity'))
        questions_score = result['total'] or 0  # لو None، خليها 0
        scoreboard[player.id] = questions_score + player.manual_adjustment
    return scoreboard

def adjust_player_score(player_id, amount):
    if amount not in [100, -100]:
        raise InvalidAdjustmentAmountError()
    
    player = Player.objects.get(id=player_id)
    player.manual_adjustment += amount
    player.save()
    return player

def get_current_session(host):
    return Session.objects.filter(host=host,status=Session.SessionStatus.INPROGRESS).first()

def abandon_session(host):
    session = Session.objects.filter(host=host,status=Session.SessionStatus.INPROGRESS).first()
    if session is None:
        raise NoActiveSessionError()
    
    with transaction.atomic():
            SessionQuestion.objects.filter(session=session).delete()
            session.delete()
    return None

def get_owned_session(host, public_id):
    return get_object_or_404(Session, public_id=public_id, host=host)

def get_owned_session_question(host, public_id):
    return get_object_or_404(SessionQuestion, public_id=public_id, session__host=host)

def get_owned_player(host, player_id):
    return get_object_or_404(Player, id=player_id, session__host=host)

def get_answer(session_question_id):
    session_question = SessionQuestion.objects.select_related('question').get(id=session_question_id)

    if session_question.state == SessionQuestion.QuestionState.LOCKED:
        raise QuestionNotOpenedError()

    question = session_question.question
    try:
        answer = question.answer
    except Answer.DoesNotExist:
        return {'text': None, 'media': None}

    media = None
    if hasattr(answer, 'media'):
        media = {'type': answer.media.media_type, 'url': answer.media.file.url}

    return {'text': answer.text, 'media': media}
