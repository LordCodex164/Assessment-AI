from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from course_module.models import Course

# Create your models here.

# create an exam model

### don't forget to add throttling

class Exam(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="exams", db_index=True
    )
    title = models.CharField(max_length=255)
    duration_minutes = models.IntegerField()
    is_active = models.BooleanField(default=True, db_index=True)
    start_time = models.DateTimeField(null=True, blank=True, db_index=True)
    end_time = models.DateTimeField(null=True, blank=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_exams"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)


class Question(models.Model):
    QUESTION_TYPES = [
        ("mcq", "Multiple Choice"),
        ("short", "Short Answer"),
        ("essay", "Essay"),
        ("true_false", "True/False"),
    ]
    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name="questions", db_index=True
    )
    text = models.CharField(max_length=255)
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPES, db_index=True, null=True
    )
    expected_answer = models.TextField()
    marks = models.PositiveIntegerField()
    # make choices field to json data array of strings
    choices = models.JSONField(
        null=True,
        blank=True,
        help_text="Applicable for MCQ type questions. Provide choices as a JSON array of strings.",
    )
    
    min_word_count = models.IntegerField(null=True, blank=True)

    keywords = models.JSONField(
        null=True,
        blank=True,
    )


    class Meta:
        ordering = ["exam"]
        indexes = [
            models.Index(fields=["exam"]),
            models.Index(fields=["exam", "question_type"]),
        ]
        verbose_name_plural = "questions"


class SubmissionQuerySet(models.QuerySet):
    def for_student(self, student):
        return self.filter(student=student)


class SubmissionManager(models.Manager.from_queryset(SubmissionQuerySet)):
    def for_student(self, student):
        return self.get_queryset().for_student(student)


class Submission(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions", db_index=True
    )
    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name="submissions", db_index=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('grading', 'Grading'),
        ('graded', 'Graded'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        db_index=True
    )
    # Denormalized score fields for fast retrieval
    total_score = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        db_index=True
    )
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        db_index=True
    )
    passed = models.BooleanField(null=True, blank=True, db_index=True)
    
    feedback = models.TextField(blank=True)

    # ✅ ADD THIS LINE - Assign the custom manager
    objects = SubmissionManager()


class SubmissionAnswer(models.Model):
    submission = models.ForeignKey(
        Submission, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    awarded_marks = models.FloatField(null=True, blank=True)
