from django.contrib import admin
from .models import Exam, Question, Submission, SubmissionAnswer

# Register your models here.

models_to_register = [Exam, Question, SubmissionAnswer, Submission]

for model in models_to_register:
    admin.site.register(model)