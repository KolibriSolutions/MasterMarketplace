from django.urls import path

from . import views

app_name = 'accesscontrol'
urlpatterns = [
    path('grant/', views.add_access, name='grant'),
    path('edit/<int:pk>/', views.edit_access, name='edit'),
    path('revoke/<int:pk>/', views.delete_access, name='revoke'),
    path('list/', views.list_access, name='list'),
    path('import/', views.import_access, name='import'),
    path('origin/add/', views.create_origin, name='createorigin'),
    path('origin/edit/<int:pk>/', views.edit_origin, name='editorigin'),
    path('origin/all/', views.list_origins, name='listorigins'),
]
