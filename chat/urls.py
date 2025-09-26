from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Chat functionality
    path('dashboard/', views.dashboard, name='dashboard'),
    path('thread/', views.chat_thread, name='new_thread'),
    path('thread/<int:thread_id>/', views.chat_thread, name='chat_thread'),
    path('send/<int:thread_id>/', views.send_message, name='send_message'),
    
    # NEW URLS FOR INDIVIDUAL CHAT DELETION
    path('delete-thread/<int:thread_id>/', views.delete_thread, name='delete_thread'),
    path('clear-chats/', views.clear_all_chats, name='clear_all_chats'),
]