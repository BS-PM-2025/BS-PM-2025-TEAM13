from django.urls import path
from . import views

app_name = 'student_chat'

urlpatterns = [
    path('chat/', views.chat_view, name='chat'),
    path('get-response/', views.get_response, name='get_response'),
]