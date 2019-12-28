from django.urls import path, re_path

from . import views

app_name = 'projects'

urlpatterns = [
    path('list/', views.list_public_projects, name='list'),
    path('favorites/', views.list_favorite_projects, name='favorites'),

    path('list/<str:type_filter>/', views.list_public_projects, name='list'),
    path('favorites/<str:type_filter>/', views.list_favorite_projects, name='favorites'),

    path('group/active/', views.list_group_projects, name='listgroupprojects'),
    path('group/<str:status_filter>/', views.list_group_projects, name='listgroupprojects'),

    path('details/<int:pk>/', views.detail_project, name='details'),
    path('create/', views.create_project, name='create'),
    path('own/active/', views.list_own_projects, name='chooseedit'),  # for if no kwargs given, default to active.
    path('own/<str:status_filter>/', views.list_own_projects, name='chooseedit'),
    path('edit/<int:pk>/', views.edit_project, name='edit'),
    path('copy/<int:pk>/', views.copy_project, name='copy'),

    path('files/add/<str:ty>/<int:pk>/', views.add_file, name='addfile'),
    path('files/edit/<str:ty>/<int:pk>/', views.edit_file, name='editfile'),

    path('delete/ask/<int:pk>/', views.ask_delete_project, name='askdeleteproject'),
    path('delete/<int:pk>/', views.delete_project, name='deleteproject'),

    path('labels/', views.list_labels, name='labels'),
    path('labels/add/', views.add_label, name='createlabel'),
    path('labels/<int:pk>/', views.edit_label, name='editlabel'),
    path('labels/activate/<int:pk>/', views.activate_label, name='activatelabel'),
    path('labels/delete/<int:pk>/', views.delete_label, name='deletelabel'),

    path('status/upgrade/<int:pk>/', views.upgrade_status, name='upgradestatus'),
    path('status/downgrade/<int:pk>/', views.downgrade_status, name='downgradestatusmessage'),

    # cpv
    path('contentpolicy/', views.content_policy_view, name='contentpolicy'),
    path('contentpolicy/calc/', views.content_policy_calc, name='contentpolicycalc'),

    path('pending/', views.list_pending, name='pending'),

    path('share/<int:pk>/', views.share, name='sharelink'),
    re_path(r'^share/(?P<token>[0-9A-Za-z_\-:]+)/$', views.view_share_link, name='viewsharelink'),

    path('distribute/<int:pk>/', views.distribute_project, name='distribute'),
    path('progress/<int:pk>/', views.progress_project, name='progress'),

    path('stats/personal/', views.project_stats_personal, name='stats_personal'),
    path('stats/active/', views.project_stats, name='stats'),  # if no kwarg.
    path('stats/<str:status_filter>/', views.project_stats, name='stats'),

]
