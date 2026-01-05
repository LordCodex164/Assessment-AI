from django.urls import path
from . import views



urlpatterns = [
    #course
    path("<int:exam_id>", views.ExamView.as_view({"get" : "retrieve"}), name='exam-detail'),
    path("<int:exam_id>/questions", views.ExamView.as_view({"post": "create_questions"}), name="question"),
    # create exam
    path("create", views.ExamView.as_view({"post": "create"}), name="exam-create"),
    #create question for exam
    path("all", views.ExamView.as_view({"get": "list"}), name="exam-list"),
    path("submissions", views.SubmissionViewSet.as_view({"get": "list"}), name="submission_view"),
    path("submissions/<int:submission_id>", views.SubmissionViewSet.as_view({"get": "retrieve_submission_answers"}), name="submission-detail"),
]