from django.urls import path
from .views import (
    SessionCreateView,SessionDetailView,PlayerAdjustScoreView,
    SessionQuestionListView,SessionQuestionOpenView,SessionQuestionJudgeView,
    ScoreboardView,
)

urlpatterns = [
    path('sessions/', SessionCreateView.as_view()),
    path('sessions/current/', SessionDetailView.as_view()),
    path('sessions/<uuid:public_id>/questions/', SessionQuestionListView.as_view()),
    path('session-questions/<uuid:public_id>/open/', SessionQuestionOpenView.as_view()),
    path('session-questions/<uuid:public_id>/judge/', SessionQuestionJudgeView.as_view()),
    path('players/<int:player_id>/adjust-score/', PlayerAdjustScoreView.as_view()),
    path('sessions/<uuid:public_id>/scoreboard/', ScoreboardView.as_view()),
]