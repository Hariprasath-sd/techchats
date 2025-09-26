import serializers
from .models import DocumentCollection, Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'filename', 'file_type', 'file_size', 'uploaded_at', 'processed', 'chunk_count']

class DocumentCollectionSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, read_only=True)
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = DocumentCollection
        fields = ['id', 'name', 'description', 'created_at', 'documents', 'document_count']

    def get_document_count(self, obj):
        return obj.documents.count()