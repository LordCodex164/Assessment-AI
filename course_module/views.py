from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Course
from .serializers import (
    CourseListSerializer,
    CourseCreateSerializer,
    CourseDetailSerializer,
)
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from grading.keyword_grader import GradingService
from django.db import transaction
from utils.responses import custom_response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from rest_framework import viewsets
import logging
from .permissions import IsStaffUser

logger = logging.getLogger(__name__)


class CourseView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [IsStaffUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        print("courses", Course.objects.all())
        return Course.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return CourseListSerializer
        elif self.action == "create":
            return CourseCreateSerializer
        return CourseDetailSerializer
    
    def list(self, request):
        print(">>> Course List Request by User:", request.user.id)
        print("quer", self.get_queryset())
        courses = self.get_queryset().only("id", "code", "name")

        serializer = self.get_serializer_class()(courses, many=True)

        return custom_response(
            data={
                "courses": serializer.data,
                "count": courses.count(),
            },
            message="Courses retrieved successfully",
            status_code=200,
        )
    
    @transaction.atomic
    def create(self, request):
        print(">>> Course Creation Request Data:", request.data)
        serializer = self.get_serializer_class()(data=request.data)

        if not serializer.is_valid():
            return custom_response(
                data=serializer.errors,
                message="Validation failed",
                status_code=400,
            )

        course = serializer.save()

        return custom_response(
            data=CourseDetailSerializer(course).data,
            message="Course created successfully",
            status_code= 201,
        )
    
    def retrieve(self, request, pk=None):
        print(">>> User", request.user.id, "requested Course ID:", pk)
        print(">>> Course Retrieve Request for ID:", pk)
        print("quer", self.get_queryset())
        # course = get_object_or_404(self.get_queryset().only(
        #     "id", "code", "name", "description"
        # ), pk=pk)
        # serializer = self.get_serializer_class()(course)

        # return custom_response(
        #     data=serializer.data,
        #     message="Course retrieved successfully",
        #     status_code=200,
        # )


