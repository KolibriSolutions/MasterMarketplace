from django.urls import path

from . import views

app_name = 'students'
urlpatterns = [
    path('applications/', views.list_applications, name='list_applications'),

    path('apply/<int:pk>/', views.apply, name='apply'),
    path('application/confirm/<int:pk>/', views.confirm_apply, name='confirmapply'),

    path('application/retract/<int:application_id>/', views.retract_application, name='retractapplication'),
    path('files/<int:dist>/', views.list_files, name='files'),
    path('files/<int:dist>/add/', views.add_file, name='addfile'),
    path('files/<int:dist>/edit/<int:file>/', views.edit_file, name='editfile'),
    # path('files/delete/<int:file>/', views.delete_file, name='deletefile'),
]
