from django.urls import path
from . views import StatsApiView, TaskListViewSet, TaskDetailViewSet
urlpatterns = [
    path('tasks/', TaskListViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('tasks/<int:id>/', TaskDetailViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('stats/', StatsApiView.as_view())
]

