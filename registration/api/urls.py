from django.urls import path

from . import views

app_name = 'registration_api'

urlpatterns = [
    path('api/planning/add_year/', views.add_year, name='api_add_year'),
    path('api/planning/remove_year/', views.remove_year, name='api_remove_year'),
    path('api/planning/save/', views.save_planning, name='api_save_planning'),
    path('api/planning/get/', views.get_planning, name='api_get_planning'),
]
