from django.contrib import admin
from .models import DocumentCollection, Document, DocumentChunk

# Register your models here.

@admin.register(DocumentCollection)
class DocumentCollectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user', 'document_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'user__username', 'description']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def document_count(self, obj):
        return obj.documents.count()
    document_count.short_description = 'Documents'

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'collection', 'file_type', 'file_size_mb', 'processed', 'chunk_count', 'uploaded_at']
    list_filter = ['file_type', 'processed', 'uploaded_at']
    search_fields = ['filename', 'collection__name', 'collection__user__username']
    readonly_fields = ['id', 'uploaded_at', 'file_size', 'chroma_collection_name']
    ordering = ['-uploaded_at']
    
    def file_size_mb(self, obj):
        return f"{obj.file_size / (1024*1024):.2f} MB"
    file_size_mb.short_description = 'Size (MB)'

@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'chunk_index', 'content_preview', 'page_number']
    list_filter = ['document__file_type']
    search_fields = ['document__filename', 'content']
    ordering = ['document', 'chunk_index']
    
    def content_preview(self, obj):
        return obj.content[:150] + "..." if len(obj.content) > 150 else obj.content
    content_preview.short_description = 'Content Preview'
