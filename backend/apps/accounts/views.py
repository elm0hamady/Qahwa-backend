from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes,force_str
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.accounts.tasks import send_user_confirmation_email
from apps.accounts.serializers import RegisterSerializer


User = get_user_model()


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        host = User.objects.create_user(
            first_name=validated['first_name'],
            last_name=validated['last_name'],
            username=validated['username'],
            email=validated['email'],
            password=validated['password'],
            is_active=False,
        )

        uid = urlsafe_base64_encode(force_bytes(host.pk))
        token = default_token_generator.make_token(host)
        verification_link = f"http://localhost:5173/verify-email/{uid}/{token}"

        send_user_confirmation_email.delay(host.username, host.email, verification_link)

        return Response(
            {"message": "Account created. Please check your email to activate your account."},
            status=status.HTTP_201_CREATED
        )


class VerifyEmailView(APIView):
    def get(self, request, uid, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            host = User.objects.get(id=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"error": "Invalid activation link."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(host, token):
            return Response(
                {"error": "Invalid or expired activation link."},
                status=status.HTTP_400_BAD_REQUEST
            )

        host.is_active = True
        host.save()

        return Response(
            {"message": "Account activated. You can sign in now and play!"},
            status=status.HTTP_200_OK
        )