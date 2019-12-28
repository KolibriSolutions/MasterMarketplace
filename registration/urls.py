from django.urls import path, include

from . import views

app_name = 'registration'
urlpatterns = [
    path('register/', views.registration_view, name='registrationform'),
    path('approve/<int:pk>/', views.approve_registration, name='approve'),
    path('disapprove/<int:pk>/', views.disapprove_registration, name='disapprove'),
    path('list/current/', views.list_registrations, name='listall'),
    path('list/<int:cohort>/', views.list_registrations, name='listall'),
    path('planner/', views.courseplanner, name='courseplanner'),
    path('planner/<int:student_pk>/', views.courseplanner, name='courseplanner'),
    path('planner/addotherdep/', views.add_other_department_course, name='addotherdep'),
    path('planner/addotheruni/', views.add_other_university_course, name='addotheruni'),
    path('stats/', views.registration_stats, name='stats'),
    path('stats/<int:cohort>', views.registration_stats, name='stats'),
    path('approval/request/', views.request_approval, name='requestapproval'),
    path('approvalform/', views.get_approvalform, name='approvalform'),
    path('approvalform/<int:pk>/', views.get_approvalform_support, name='approvalformsupport'),

    path('deadlines/<int:t>/', views.deadline_form, name='deadlineform'),
    path('deadlines/', views.deadlines, name='deadlines'),
    path('deadlines/description', views.deadline_description_form, name='deadlinedescription'),

    path('api/', include('registration.api.urls')),
]
