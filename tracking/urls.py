from django.urls import path

from . import views

app_name = 'tracking'
urlpatterns = [
    path('user/login/', views.list_user_login, name='listuserlog'),
    path('user/<int:pk>/', views.telemetry_user_detail, name='userdetail'),
    path('project/', views.list_project_status_change, name='statuslist'),
    path('application/', views.list_application_change, name='applicationlist'),
    path('distribution/', views.list_distribution_change, name='distributionslist'),
    path('registration/', views.list_registration_changes, name='registrationchanges'),
]
