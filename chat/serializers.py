import serializers
from .models import ChatThread, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'content', 'is_user', 'timestamp', 'is_rag_response', 'source_documents']

class ChatThreadSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatThread
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages', 'message_count']

    def get_message_count(self, obj):
        return obj.messages.count()
