from django.urls import path
from . import views

urlpatterns = [
    path('documents/', views.documents, name='documents'),
    path('create-collection/', views.create_collection, name='create_collection'),
    path('collection/<int:collection_id>/', views.collection_detail, name='collection_detail'),
    path('upload/<int:collection_id>/', views.upload_document, name='upload_document'),
    path('delete-document/<uuid:document_id>/', views.delete_document, name='delete_document'),
    path('delete-collection/<int:collection_id>/', views.delete_collection, name='delete_collection'),
]