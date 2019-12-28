from django.urls import path

from . import views

app_name = 'godpowers'
urlpatterns = [
    path('clearcache/', views.clear_cache, name='clearcache'),
    path('sessions/list/', views.list_sessions, name='sessionlist'),
    path('sessions/kill/<int:pk>/', views.kill_session, name='killsession'),
]
