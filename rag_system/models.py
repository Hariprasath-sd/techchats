from django.db import models
from django.contrib.auth.models import User
import uuid

class DocumentCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    collection = models.ForeignKey(DocumentCollection, on_delete=models.CASCADE, related_name='documents')
    filename = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='documents/')
    file_type = models.CharField(max_length=10)
    file_size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    chroma_collection_name = models.CharField(max_length=100, blank=True)
    chunk_count = models.IntegerField(default=0)

    def __str__(self):
        return self.filename

class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()
    chunk_index = models.IntegerField()
    page_number = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ['document', 'chunk_index']