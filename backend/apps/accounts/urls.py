from django.urls import path
from .views import RegisterView,VerifyEmailView

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('verify-email/<str:uid>/<str:token>/', VerifyEmailView.as_view())
]