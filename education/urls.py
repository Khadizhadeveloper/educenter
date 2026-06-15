from django.urls import path
from . import views

urlpatterns = [


    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),


    path('dashboard/', views.dashboard, name='dashboard'),


    path('schedule/', views.schedule_view, name='schedule'),


    path('homework/', views.homework_list, name='homework_list'),
    path('homework/submit/<int:homework_id>/', views.homework_submit, name='homework_submit'),


    path('mentor/dashboard/', views.mentor_dashboard, name='mentor_dashboard'),
    path('mentor/homework/add/', views.mentor_create_homework, name='mentor_create_homework'),
    path('mentor/lesson/add/', views.mentor_create_lesson, name='mentor_create_lesson'),
    path('mentor/grade/add/', views.mentor_give_grade, name='mentor_give_grade'),
    path('mentor/lesson/<int:lesson_id>/attendance/', views.mentor_attendance, name='mentor_attendance'),
    path('mentor/homework/<int:homework_id>/submissions/', views.mentor_homework_submissions, name='mentor_homework_submissions'),
    path('mentor/submission/<int:submission_id>/review/',  views.mentor_review_submission,    name='mentor_review_submission'),

    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),


    path('grades/', views.grades_view, name='grades'),


    path('admin-panel/users/', views.admin_user_list, name='admin_user_list'),
    path('admin-panel/users/create/', views.admin_create_user, name='admin_create_user'),
    path('admin-panel/users/<int:user_id>/role/', views.admin_assign_role, name='admin_assign_role'),
    path('admin-panel/users/<int:user_id>/mentor-profile/', views.admin_mentor_profile, name='admin_mentor_profile'),
    path('admin-panel/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),

    # Notifications
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),

    # KPI
    path('kpi/',         views.student_kpi_view, name='student_kpi'),
    path('kpi/mentor/',  views.mentor_kpi_view,  name='mentor_kpi'),
    path('kpi/admin/',   views.admin_kpi_view,   name='admin_kpi'),

    # Tests — student
    path('tests/course/<int:course_id>/',   views.test_topic_list,  name='test_topic_list'),
    path('tests/take/<int:test_id>/',        views.test_take,         name='test_take'),
    path('tests/result/<int:attempt_id>/',   views.test_result,       name='test_result'),
    path('tests/my/',                        views.test_my_results,   name='test_my_results'),

    # Tests — mentor management
    path('mentor/tests/course/<int:course_id>/',          views.mentor_topic_list,    name='mentor_topic_list'),
    path('mentor/tests/course/<int:course_id>/topic/new/', views.mentor_topic_create,  name='mentor_topic_create'),
    path('mentor/tests/topic/<int:topic_id>/test/new/',   views.mentor_test_create,   name='mentor_test_create'),
    path('mentor/tests/test/<int:test_id>/edit/',          views.mentor_test_edit,     name='mentor_test_edit'),
    path('mentor/tests/test/<int:test_id>/questions/add/', views.mentor_question_add,  name='mentor_question_add'),
    path('mentor/tests/question/<int:question_id>/edit/',  views.mentor_question_edit, name='mentor_question_edit'),
    path('mentor/tests/test/<int:test_id>/results/',       views.mentor_test_results,  name='mentor_test_results'),
]