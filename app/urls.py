from django.urls import path
from . views import TaskListApiView, TaskDetailApiView, StatsApiView
urlpatterns = [
    path('tasks/', TaskListApiView.as_view()),
    path('tasks/<int:id>/', TaskDetailApiView.as_view()),
    path('stats/', StatsApiView.as_view())
]

