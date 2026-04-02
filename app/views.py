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

class TaskListApiView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated | IsAnonymous]
    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)
    def get_serializer_class(self):
        if self.request.method == "POST":
            return TaskValidateSerializer
        return TaskListSerializer
    def get(self, request):
        search_query = request.query_params.get('search', None)
        if search_query:
            queryset = self.get_queryset().filter(title__icontains=search_query)
            serializer = TaskListSerializer(queryset, many=True)
            return Response(serializer.data)
        status_query = request.query_params.get('status', None)
        if status_query:
            queryset = self.get_queryset().filter(status=status_query)
            serializer = TaskListSerializer(queryset, many=True)
            return Response(serializer.data)
        tasks = self.get_queryset()
        data = TaskListSerializer(tasks, many=True).data
        return Response(
            data=data,
        )
    def perform_create(self, serializer):
            title = serializer.validated_data.get('title')
            description = serializer.validated_data.get('description')
            task_status = serializer.validated_data.get('task_status')
            with transaction.atomic():       
                task = Task.objects.create(
                    title=title,
                    description=description,
                    status=task_status,
                    owner=self.request.user
                    )
            return Response(status=status.HTTP_201_CREATED,
                    data=TaskListSerializer(task).data)

class TaskDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [(permissions.IsAuthenticated & IsOwner)]
    queryset = Task.objects.all()
    lookup_field = 'id'
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TaskValidateSerializer
        return TaskDetailSerializer
    def perform_update(self, serializer):
        serializer.save()
    
class StatsApiView(APIView):
    def get(self, request):
        tasks = Task.objects.filter(owner=request.user)
        stats = tasks.aggregate(
            total=Count('id'),
            done=Count('id', filter=Q(status='done')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            todo=Count('id', filter=Q(status='todo')))
        return Response(stats)

