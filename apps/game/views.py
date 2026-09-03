from rest_framework.views import APIView
from rest_framework import generics 
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from core.exceptions import (
    SessionAlreadyActiveError,InvalidAdjustmentAmountError,InvalidTopicCountError,PlayerNotInSessionError,
    DuplicateTopicError,QuestionAlreadyJudgedError,QuestionAlreadyOpenedError,NoActiveSessionError,
    InsufficientQuestionPoolError
)
from .services import (
    start_session,get_current_session ,get_scoreboard,get_owned_player,
    adjust_player_score,judge_question,abandon_session,get_owned_session,
    get_owned_session_question,open_question
)
from .serializers import (
    SessionSerializer,SessionQuestionSerializer,
    ScoreboardEntrySerializer,StartSessionInputSerializer,AdjustScoreInputSerializer,JudgeQuestionInputSerializer   
)

class SessionCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        input_serializer = StartSessionInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        validated  = input_serializer.validated_data
        try:
            session = start_session(
                host=request.user,
                player1_name=validated['player1_name'],
                player2_name=validated['player2_name'],
                topic_ids=validated['topic_ids'],
            )
        except SessionAlreadyActiveError:
            return Response({"error": "You already have an active session."}, status=status.HTTP_409_CONFLICT)
        except InvalidTopicCountError:
            return Response({"error": "Exactly 4 topics required."}, status=status.HTTP_400_BAD_REQUEST)
        except DuplicateTopicError:
            return Response({"error": "Duplicate topics are not allowed."}, status=status.HTTP_400_BAD_REQUEST)
        except InsufficientQuestionPoolError:
            return Response({"error": "Selected topic doesn't have enough questions."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SessionSerializer(session)
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class SessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session = get_current_session(host=request.user)
        if session is None:
            return Response({"session": None}, status=status.HTTP_200_OK)
        serializer = SessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        try:
            abandon_session(host=request.user)
        except NoActiveSessionError:
            return Response({"error": "No active session to abandon."}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

class SessionQuestionListView(generics.ListAPIView):
    serializer_class = SessionQuestionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None 

    def get_queryset(self):
        public_id = self.kwargs.get('public_id')
        session = get_owned_session(host=self.request.user,public_id=public_id)
        return session.sessionquestion_set.select_related(
        'question__topic', 'assigned_player', 'question__media'
    ).all()


class SessionQuestionOpenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        session_question = get_owned_session_question(host=request.user, public_id=public_id)
        try:
            session_question = open_question(session_question.id) 
        except QuestionAlreadyOpenedError:
            return Response({"error": "You already opened this question."}, status=status.HTTP_409_CONFLICT)
        serializer = SessionQuestionSerializer(session_question)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SessionQuestionJudgeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, public_id):
        session_question = get_owned_session_question(host=request.user, public_id=public_id)

        input_serializer = JudgeQuestionInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        winner_player_id = input_serializer.validated_data.get('winner_player_id')

        try:
            session_question = judge_question(session_question.id, winner_player_id)
        except QuestionAlreadyJudgedError:
            return Response({"error": "Question already judged before."}, status=status.HTTP_409_CONFLICT)
        except PlayerNotInSessionError:
            return Response({"error": "Player is not part of this session."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SessionQuestionSerializer(session_question)
        data = serializer.data
        data['session_finished'] = session_question.session.status == session_question.session.SessionStatus.FINISHED

        return Response(data, status=status.HTTP_200_OK)

class PlayerAdjustScoreView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request,player_id):
        player = get_owned_player(request.user,player_id)

        input_serializer = AdjustScoreInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        amount = input_serializer.validated_data.get('amount')
        try:
            player = adjust_player_score(player_id,amount)
        except InvalidAdjustmentAmountError:
            return Response({"error": "Amount should be +100 or -100."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"id": player.id, "name": player.name, "manual_adjustment": player.manual_adjustment},
            status=status.HTTP_200_OK
        )

class ScoreboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, public_id):
        session = get_owned_session(host=request.user, public_id=public_id)
        scores = get_scoreboard(session)  # {player_id: score}

        entries = []
        for player in session.player_set.all():
            entries.append({
                'player_id': player.id,
                'player_name': player.name,
                'score': scores[player.id]
            })

        serializer = ScoreboardEntrySerializer(entries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        