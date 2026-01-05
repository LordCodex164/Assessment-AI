
from rest_framework import serializers
from .models import Course


class CourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "code", "name", "description")


class CourseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "code", "name", "description")


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("code", "name", "description")