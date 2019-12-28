from django.urls import path

from . import views

app_name = 'support'
urlpatterns = [
    path('mail/', views.mailing, name='mailinglist'),
    path('mail/templates/<int:pk>/', views.mailing, name='mailinglisttemplate'),
    path('mail/confirm', views.confirm_mailing, name='mailingconfirm'),
    path('mail/templates/', views.list_mailing_templates, name='mailingtemplates'),
    path('mail/templates/delete/<int:pk>/', views.delete_mailing_template, name='deletemailingtemplate'),

    path('promotions/add/', views.add_promotion, name='addpromotion'),
    path('promotions/edit/', views.edit_promotion, name='editpromotions'),

    # path('promotions/add/', views.add_promotion, name='addpromotion'),
    path('menulinks/edit/', views.edit_menu_links, name='editmenulinks'),

    path('users/', views.list_users, name='listusers'),
    path('users/<int:pk>', views.user_info, name='userinfo'),
    # path('users/clearcache', views.list_users_clear_cache, name='clearcacheuserlist'),
    path('users/groups/<int:pk>/', views.edit_user_groups, name='usergroups'),
    path('user/toggle/<int:pk>/', views.toggle_disable_user, name='toggledisable'),

    path('groupadministrator/', views.groupadministrators_form, name='groupadministratorsform'),

    path('staff/', views.list_staff, name='liststaff'),
    path('staff/projects/<int:pk>/', views.list_staff_projects, name='liststaffprojects'),
    path('students/', views.list_students, name='liststudents'),

    # path('projects/group/', views.list_group_projects, name='listgroupprojects'),
    # path('projects/studyadvisor/', views.list_studyadvisor_projects, name='listprojectsadvisor'),
    # path('registration/stats/<int:step>', views.registration_stats, name='registrationstats'),

]
