from django.contrib import admin
from .models import ChatThread, Message

@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'message_count', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'title']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'thread', 'user_name', 'is_user', 'is_rag_response', 'content_preview', 'timestamp']
    list_filter = ['is_user', 'is_rag_response', 'timestamp']
    search_fields = ['thread__user__username', 'content']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def user_name(self, obj):
        return obj.thread.user.username
    user_name.short_description = 'User'
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'