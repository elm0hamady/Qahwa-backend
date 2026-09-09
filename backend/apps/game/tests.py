from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.game.models import Session,Player,SessionQuestion
from apps.bank.models import Category,Topic,Question
from apps.game.services import validate_start_session,start_session,open_question,judge_question
from core.exceptions import (
    SessionAlreadyActiveError,InsufficientQuestionPoolError,
    QuestionAlreadyOpenedError,QuestionAlreadyJudgedError
)
User = get_user_model()


class ValidateStartSessionTests(TestCase):

    def setUp(self):
        self.host = User.objects.create_user(username='test',password='test')
        self.session =Session.objects.create(host=self.host)

    def test_raises_if_host_already_has_active_session(self):
        with self.assertRaises(SessionAlreadyActiveError):
            validate_start_session(host=self.host, topic_ids=[1, 2, 3, 4])

class InsufficientQuestionPoolTests(TestCase):

    def setUp(self):
        self.host = User.objects.create_user(username='test2', password='test')
        category = Category.objects.create(name='Sports')

        self.complete_topics = []
        for i in range(3):
            topic = Topic.objects.create(name=f'Complete Topic {i}', category=category)
            for difficulty in [100, 300, 500]:
                Question.objects.create(topic=topic, difficulity=difficulty, text=f'Q1-{i}-{difficulty}')
                Question.objects.create(topic=topic, difficulity=difficulty, text=f'Q2-{i}-{difficulty}')
            self.complete_topics.append(topic)

        self.incomplete_topic = Topic.objects.create(name='Incomplete Topic', category=category)
        Question.objects.create(topic=self.incomplete_topic, difficulity=100, text='Only one question')

        for difficulty in [300, 500]:
            Question.objects.create(topic=self.incomplete_topic, difficulity=difficulty, text=f'Q1-{difficulty}')
            Question.objects.create(topic=self.incomplete_topic, difficulity=difficulty, text=f'Q2-{difficulty}')

    def test_raises_when_topic_missing_questions(self):
        topic_ids = [t.id for t in self.complete_topics] + [self.incomplete_topic.id]
        with self.assertRaises(InsufficientQuestionPoolError):
            validate_start_session(host=self.host, topic_ids=topic_ids)


class StartSessionSuccessTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username='test3', password='test')
        category = Category.objects.create(name='Sports')
        

        self.complete_topics = []
        for i in range(4):
            topic = Topic.objects.create(name=f'Complete Topic {i}', category=category)
            for difficulty in [100, 300, 500]:
                Question.objects.create(topic=topic, difficulity=difficulty, text=f'Q1-{i}-{difficulty}')
                Question.objects.create(topic=topic, difficulity=difficulty, text=f'Q2-{i}-{difficulty}')
            self.complete_topics.append(topic)

    def test_creates_correct_number_of_records(self):
        player1 = 'nametest1'
        player2 = 'nametest2'
        topic_ids = [t.id for t in self.complete_topics]
        start_session(host=self.host,player1_name=player1,player2_name=player2,topic_ids=topic_ids)
        self.assertEqual(Session.objects.count(), 1)
        self.assertEqual(Player.objects.count(), 2)
        self.assertEqual(SessionQuestion.objects.count(), 24)

class OpenQuestionTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Sports')
        self.topic = Topic.objects.create(name=f'Complete Topic 0', category=self.category)
        self.host = User.objects.create_user(username='test',password='test')
        self.session =Session.objects.create(host=self.host)
        self.question = Question.objects.create(topic=self.topic, difficulity=100, text=f'Q1-')
        self.player = Player.objects.create(name='ahmed',session=self.session)
        self.session_question = SessionQuestion.objects.create(
            assigned_player=self.player,question=self.question,
            session=self.session,state=SessionQuestion.QuestionState.OPENED
            )
    def test_raise_if_question_already_opened(self):
        with self.assertRaises(QuestionAlreadyOpenedError):
            open_question(self.session_question.id)


class JudgeQuestionTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Sports')
        self.topic = Topic.objects.create(name='Topic 0', category=self.category)
        self.host = User.objects.create_user(username='judgehost', password='test')
        self.session = Session.objects.create(host=self.host)
        self.question = Question.objects.create(topic=self.topic, difficulity=100, text='Q1')
        self.question2 = Question.objects.create(topic=self.topic, difficulity=100, text='Q2')
        self.player = Player.objects.create(name='Ahmed', session=self.session)
        self.session_question1 = SessionQuestion.objects.create(
            assigned_player=self.player, question=self.question,
            session=self.session, state=SessionQuestion.QuestionState.JUDGED
        )
        self.session_question2 = SessionQuestion.objects.create(
                    assigned_player=self.player, question=self.question2,
                    session=self.session, state=SessionQuestion.QuestionState.OPENED
                )
    def test_raises_if_already_judged(self):
        with self.assertRaises(QuestionAlreadyJudgedError):
            judge_question(self.session_question1.id, winner_player_id=self.player.id)

    def test_finishes_session_when_last_question_judged(self):
        judge_question(self.session_question2.id, winner_player_id=self.player.id)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status,'finished')