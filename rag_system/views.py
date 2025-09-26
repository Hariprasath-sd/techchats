from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import os
from .models import DocumentCollection, Document
from .services import DocumentProcessingService

@login_required
def documents(request):
    collections = DocumentCollection.objects.filter(user=request.user)
    return render(request, 'rag/documents.html', {'collections': collections})

@login_required
def create_collection(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            DocumentCollection.objects.create(
                user=request.user,
                name=name,
                description=description
            )
            messages.success(request, f'Collection "{name}" created successfully!')
            return redirect('documents')
        else:
            messages.error(request, 'Collection name is required.')
    
    return render(request, 'rag/create_collection.html')

@login_required
def upload_document(request, collection_id):
    collection = get_object_or_404(DocumentCollection, id=collection_id, user=request.user)
    
    if request.method == 'POST':
        file = request.FILES.get('file')
        if file:
            allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
            file_extension = os.path.splitext(file.name)[1].lower()
            
            if file_extension not in allowed_extensions:
                messages.error(request, 'File type not supported.')
                return render(request, 'rag/upload.html', {'collection': collection})
            
            if file.size > 10 * 1024 * 1024:
                messages.error(request, 'File too large. Maximum 10MB.')
                return render(request, 'rag/upload.html', {'collection': collection})
            
            try:
                document = Document.objects.create(
                    collection=collection,
                    filename=file.name,
                    file_path=file,
                    file_type=file_extension[1:],
                    file_size=file.size
                )
                
                doc_service = DocumentProcessingService()
                success = doc_service.process_document(document)
                
                if success:
                    messages.success(request, f'Document "{file.name}" processed successfully!')
                else:
                    messages.warning(request, f'Document uploaded but processing failed.')
                
            except Exception as e:
                messages.error(request, f'Error uploading document: {str(e)}')
            
            return redirect('collection_detail', collection_id=collection_id)
        else:
            messages.error(request, 'Please select a file.')
    
    return render(request, 'rag/upload.html', {'collection': collection})

@login_required
def collection_detail(request, collection_id):
    collection = get_object_or_404(DocumentCollection, id=collection_id, user=request.user)
    documents = collection.documents.all().order_by('-uploaded_at')
    
    return render(request, 'rag/collection_detail.html', {
        'collection': collection,
        'documents': documents
    })

@csrf_exempt
@login_required  
def delete_document(request, document_id):
    if request.method == 'POST':
        try:
            document = get_object_or_404(Document, id=document_id, collection__user=request.user)
            filename = document.filename
            
            if document.file_path:
                try:
                    default_storage.delete(document.file_path.name)
                except:
                    pass
            
            document.delete()
            
            return JsonResponse({
                'success': True, 
                'message': f'Document "{filename}" deleted successfully.'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

@login_required
def delete_collection(request, collection_id):
    collection = get_object_or_404(DocumentCollection, id=collection_id, user=request.user)
    
    if request.method == 'POST':
        collection_name = collection.name
        
        for document in collection.documents.all():
            if document.file_path:
                try:
                    default_storage.delete(document.file_path.name)
                except:
                    pass
        
        collection.delete()
        messages.success(request, f'Collection "{collection_name}" deleted successfully!')
        return redirect('documents')
    
    return render(request, 'rag/delete_collection.html', {'collection': collection})