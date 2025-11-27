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


    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),


    path('grades/', views.grades_view, name='grades'),

]