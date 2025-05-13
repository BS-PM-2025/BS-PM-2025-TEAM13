from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Conversation(models.Model):
    # שנה את השורה הזו
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"שיחה מ-{self.created_at.strftime('%d/%m/%Y')}"


class Message(models.Model):
    SENDER_CHOICES = (
        ('user', 'משתמש'),
        ('bot', 'בוט'),
    )
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_sender_display()}: {self.content[:30]}"