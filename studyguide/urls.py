from django.urls import path

from . import views

app_name = 'studyguide'
urlpatterns = [
    path('courses/list/', views.list_courses, name='courseslist'),
    path('years/', views.list_years, name='yearslist'),
    path('courses/list/<int:year>/', views.list_courses, name='courseslist'),

    path('masterprogram/add/', views.add_master_program, name='addmasterprogram'),
    path('masterprogram/edit/<int:pk>/', views.edit_master_program, name='editmasterprogram'),
    path('masterprogram/delete/<int:pk>/', views.delete_master_program, name='deletemasterprogram'),
    path('masterprogram/list/', views.list_master_programs, name='masterprogramlist'),
    path('masterprogram/list/<int:year>/', views.list_master_programs, name='masterprogramlist'),
    path('masterprogram/detail/<int:pk>/', views.detail_master_program, name='detailmasterprogram'),
    path('masterprogram/images/<int:pk>/', views.edit_master_program_images, name='editmasterprogramimages'),
    path('masterprogram/images/<int:pk>/add/', views.add_master_program_image, name='addmasterprogramimage'),

    # new naming for masterprogram
    path('path/add/', views.add_master_program, name='addpath'),
    path('path/edit/<int:pk>/', views.edit_master_program, name='editpath'),
    path('path/delete/<int:pk>/', views.delete_master_program, name='deletepath'),
    path('path/list/', views.list_master_programs, name='pathslist'),
    path('path/list/<int:year>/', views.list_master_programs, name='pathslist'),
    path('path/detail/<int:pk>/', views.detail_master_program, name='detailpath'),

    path('capacitygroup/add/', views.add_capacity_group, name='addcapacitygroup'),
    path('capacitygroup/edit/<int:pk>/', views.edit_capacity_group, name='editcapacitygroup'),
    path('capacitygroup/delete/<int:pk>/', views.delete_capacity_group, name='deletecapacitygroup'),
    path('capacitygroup/detail/<int:pk>/', views.detail_capacity_group, name='detailcapacitygroup'),
    path('capacitygroup/detail/<str:shortname>/', views.detail_capacity_group_name, name='detailcapacitygroup'),
    path('capacitygroup/list/', views.list_capacity_groups, name='listcapacitygroups'),
    path('capacitygroup/images/<int:pk>/', views.edit_capacity_group_images, name='editcapacitygroupimages'),
    path('capacitygroup/images/<int:pk>/add/', views.add_capacity_group_images, name='addcapacitygroupimage'),

    path('admin/course/create/', views.main_course_form_view, name='maincourseadd'),
    path('admin/course/edit/<slug:code>/<int:year>/', views.main_course_form_view, name='maincourseedit'),
    path('admin/course/delete/<slug:code>/<int:year>/', views.delete_main_course, name='maincoursedelete'),

]
