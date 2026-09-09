from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


@shared_task
def send_user_confirmation_email(
    username,
    user_email,
    verification_link,
):
    subject = "Confirm your email address"

    html_message = render_to_string(
        "emails/verify_email.html",
        {
            "username": username,
            "verification_link": verification_link,
        },
    )

    text_message = (
        f"Welcome, {username}!\n\n"
        "We're excited to have you with us!\n\n"
        "Please confirm your email by clicking the link below:\n\n"
        f"{verification_link}\n\n"
        "If you don't see this email in your inbox, "
        "please check your Spam or Junk folder.\n\n"
        "Welcome aboard!\n"
        "The Qahwa Team"
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email],
    )

    email.attach_alternative(html_message, "text/html")

    return email.send()