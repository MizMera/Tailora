from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('', views.support_page_view, name='support_page'),
    path('api/chat/', views.support_chat_api, name='chat_api'),
]
