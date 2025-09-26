from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from .models import ChatThread, Message
from .services import ChatService
from rag_system.models import DocumentCollection

logger = logging.getLogger(__name__)

# Authentication Views
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        email = request.POST.get('email', '').strip()
        
        if not username or not password or not email:
            messages.error(request, 'All fields are required.')
            return render(request, 'auth/signup.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'auth/signup.html')
        
        try:
            User.objects.create_user(username=username, password=password, email=email)
            messages.success(request, f'Welcome {username}! Account created successfully.')
            return redirect('login')
        except Exception as e:
            messages.error(request, 'Error creating account. Please try again.')
    
    return render(request, 'auth/signup.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'auth/login.html')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials.')
    
    return render(request, 'auth/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')

# Dashboard
@login_required
def dashboard(request):
    threads = ChatThread.objects.filter(user=request.user).order_by('-updated_at')[:20]
    collections = DocumentCollection.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'chat/dashboard.html', {
        'threads': threads,
        'collections': collections
    })

@login_required
def chat_thread(request, thread_id=None):
    if thread_id:
        thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
        messages_list = thread.messages.all()
    else:
        thread = ChatThread.objects.create(user=request.user, title="New Conversation")
        messages_list = []
    
    collections = DocumentCollection.objects.filter(
        user=request.user, documents__processed=True
    ).distinct()
    
    return render(request, 'chat/thread.html', {
        'thread': thread,
        'messages': messages_list,
        'collections': collections
    })

@csrf_exempt
@login_required
def send_message(request, thread_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        use_rag = data.get('use_rag', False)
        collection_id = data.get('collection_id')
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Message required.'})
        
        thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
        
        # Save user message
        user_message = Message.objects.create(
            thread=thread,
            content=content,
            is_user=True
        )
        
        # Generate AI response
        chat_service = ChatService()
        if use_rag and collection_id:
            ai_response, sources = chat_service.generate_rag_response(
                content, collection_id, request.user
            )
            ai_message = Message.objects.create(
                thread=thread,
                content=ai_response,
                is_user=False,
                is_rag_response=True,
                source_documents=sources
            )
        else:
            history = thread.messages.order_by('-timestamp')[:10]
            ai_response = chat_service.generate_response(content, history)
            ai_message = Message.objects.create(
                thread=thread,
                content=ai_response,
                is_user=False
            )
            sources = []
        
        # Update thread title if it's the first user message
        if thread.messages.filter(is_user=True).count() == 1:
            thread.title = content[:50] + ("..." if len(content) > 50 else "")
            thread.save()
        
        return JsonResponse({
            'success': True,
            'user_message': {
                'content': user_message.content,
                'timestamp': user_message.timestamp.strftime('%H:%M')
            },
            'ai_message': {
                'content': ai_message.content,
                'timestamp': ai_message.timestamp.strftime('%H:%M'),
                'is_rag_response': ai_message.is_rag_response,
                'sources': sources
            }
        })
        
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred while processing your message.'})

# NEW FUNCTIONS FOR INDIVIDUAL CHAT DELETION
@csrf_exempt
@login_required
def delete_thread(request, thread_id):
    """Delete individual chat thread - MAIN NEW FUNCTIONALITY"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        thread = get_object_or_404(ChatThread, id=thread_id, user=request.user)
        thread_title = thread.title or "New Conversation"
        
        # Delete the thread (messages will cascade delete due to foreign key)
        thread.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'Chat "{thread_title}" deleted successfully',
            'thread_id': thread_id
        })
    except ChatThread.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Chat not found'})
    except Exception as e:
        logger.error(f"Error deleting thread {thread_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Failed to delete chat'})

@csrf_exempt
@login_required
def clear_all_chats(request):
    """Clear all chat history for the user"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        count = ChatThread.objects.filter(user=request.user).count()
        ChatThread.objects.filter(user=request.user).delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'{count} conversations deleted',
            'count': count
        })
    except Exception as e:
        logger.error(f"Error clearing all chats for user {request.user.id}: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Failed to clear chats'})