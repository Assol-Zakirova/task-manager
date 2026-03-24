from rest_framework import serializers
from .models import Task
from django.contrib.auth.models import User

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")

        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError("User already exists")

        return attrs

class TaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = 'title description owner'.split()

class TaskValidateSerializer(serializers.Serializer):
    title = serializers.CharField(required=True, min_length=1, max_length=255)
    description = serializers.CharField(required=False, default='No text')
    task_status = serializers.CharField(required=True)

    def validate(self, attrs):
        status = attrs.get('task_status')

        if status and attrs['task_status'] not in ['todo', 'in_progress', 'done']:
            raise serializers.ValidationError("You cannot use such status")
        return attrs

class TaskDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
