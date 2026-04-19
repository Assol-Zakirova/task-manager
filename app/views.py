from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction
from . serializers import RegisterSerializer, TaskListSerializer, TaskValidateSerializer, TaskDetailSerializer
from . models import Task
from django.db.models import Count, Q
from . permsissions import IsAnonymous, IsOwner
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
    
class RegisterApiView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                password=password,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "message": "User created",
                "token": token.key
            },
            status=status.HTTP_201_CREATED,
            
        )
    
class TaskListViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status']
    search_fields = ['title']

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskValidateSerializer
        return TaskListSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class TaskDetailViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated & IsOwner]
    queryset = Task.objects.all()
    lookup_field = 'id'
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return TaskValidateSerializer
        return TaskDetailSerializer
    def perform_update(self, serializer):
        serializer.save(owner=self.request.user)

    
class StatsApiView(APIView):
    def get(self, request):
        tasks = Task.objects.filter(owner=request.user)
        stats = tasks.aggregate(
            total=Count('id'),
            done=Count('id', filter=Q(status='done')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            todo=Count('id', filter=Q(status='todo')))
        return Response(stats)

