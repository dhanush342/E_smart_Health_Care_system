from django.urls import path
from appointment import views

urlpatterns = [
    path('', views.rl_benchmark_view, name='appointment'),
    path('benchmark/', views.rl_benchmark_view, name='rl_benchmark'),
    path('optimize/', views.rl_optimize_schedule_view, name='rl_optimize_schedule'),
]
