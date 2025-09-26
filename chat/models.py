from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ChatThread(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title or 'Untitled'}"

class Message(models.Model):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    is_user = models.BooleanField(default=True)
    timestamp = models.DateTimeField(default=timezone.now)
    is_rag_response = models.BooleanField(default=False)
    source_documents = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{'User' if self.is_user else 'AI'}: {self.content[:50]}..."