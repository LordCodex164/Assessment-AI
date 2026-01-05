from django.urls import path
from . import views


urlpatterns = [
    path("<int:course_id>", views.CourseView.as_view({"get" : "retrieve"}), name='course-detail'),
    path("", views.CourseView.as_view({"post": "create"}), name="course-create"),
    path("all", views.CourseView.as_view({"get": "list"}), name="course-list"),
]