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
class RegisterApiView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
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
                "token": token.key,
            },                status=status.HTTP_201_CREATED
        )
class TaskListApiView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            tasks = Task.objects.filter(owner=request.user)
        else:
            return Response(
                data={'error': 'user is not authenticated'},
                status=status.HTTP_404_NOT_FOUND)
        search_query = request.query_params.get('search', None)
        if search_query:
            queryset = tasks.filter(title__icontains=search_query)
            serializer = TaskListSerializer(queryset, many=True)
            return Response(serializer.data)
        status_query = request.query_params.get('status', None)
        if status_query:
            queryset = tasks.filter(status=status_query)
            serializer = TaskListSerializer(queryset, many=True)
            return Response(serializer.data)

        data = TaskListSerializer(tasks, many=True).data
        return Response(
            data=data,
        )
    def post(self, request):
        if request.user.is_authenticated:

            serializer = TaskValidateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data=serializer.errors)
            title = serializer.validated_data.get('title')
            description = serializer.validated_data.get('description')
            task_status = serializer.validated_data.get('task_status')
            with transaction.atomic():       
                task = Task.objects.create(
                    title=title,
                    description=description,
                    status=task_status,
                    owner=request.user
                    )
            return Response(status=status.HTTP_201_CREATED,
                    data=TaskListSerializer(task).data)
        else:
            return Response(
                data={'error': 'user is not authenticated'},
                status=status.HTTP_404_NOT_FOUND)

class TaskDetailApiView(APIView):
    def get_object(self, id):
        try:
            return Task.objects.get(id=id)
        except Task.DoesNotExist:
            return None
    def get(self, request, id):
        task = self.get_object(id)
        if task is None:
            return Response(
                data={'error': 'task not found!'},
                status=status.HTTP_404_NOT_FOUND
            )
        data = TaskDetailSerializer(task, many=False).data
        return Response(data=data)
    def put(self, request, id):
        task = self.get_object(id)
        if task is None:
            return Response(
                data={'error': 'task not found!'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = TaskValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task.title = request.data.get('title')
        task.description = request.data.get('description')
        task.status = request.data.get('task_status')
        task.save()
        return Response(data=TaskDetailSerializer(task).data,
                        status=status.HTTP_201_CREATED)
    def delete(self, request, id):
        task = self.get_object(id)
        if task is None:
            return Response(
                data={'error': 'task not found!'},
                status=status.HTTP_404_NOT_FOUND
            )
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class StatsApiView(APIView):
    def get(self, request):
        tasks = Task.objects.filter(owner=request.user)
        stats = tasks.aggregate(
            total=Count('id'),
            done=Count('id', filter=Q(status='done')),
            in_progress=Count('id', filter=Q(status='in_progress')),
            todo=Count('id', filter=Q(status='todo')))
        return Response(stats)

