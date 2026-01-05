from django.utils import timezone
from .models import Exam, Question, Submission, SubmissionAnswer, Course
from .serializers import (
    QuestionSerializer,
    SubmissionListSerializer,
    ExamDetailSerializer,
    SubmissionDetailSerializer,
    SubmissionCreateSerializer,
    ExamListSerializer,
    ExamCreateSerializer,
    QuestionCreateSerializer,
    BulkQuestionCreateSerializer,
)
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from grading.keyword_grader import GradingService
from django.db import transaction
from utils.responses import custom_response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.db.models import Prefetch
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Avg, Q
from rest_framework import viewsets
from decimal import Decimal
import logging
from rest_framework.decorators import action
from .permissions import IsStaffUser

logger = logging.getLogger(__name__)


# Create your views here.
class ExamView(viewsets.ViewSet):
    """
    HIGHLY OPTIMIZED ViewSet for managing user exam details
    """

    def get_permissions(self):
        """
        Instantiate and return the list of permissions
        """
        if self.action in ["create", "create_questions", "bulk_create_questions"]:
            permission_classes = [IsStaffUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "list":
            return ExamListSerializer
        elif self.action == "create":
            return ExamCreateSerializer
        elif self.action in ["create_questions", "bulk_create_questions"]:
            return QuestionCreateSerializer
        return ExamDetailSerializer

    def get_queryset(self):
        return Exam.objects.filter(is_active=True)

    def get_serializer_class(self):
        if self.action == "list":
            return ExamListSerializer
        return ExamDetailSerializer

    def get_queryset(self):
        return Exam.objects.filter(is_active=True)

    # create a list method that creates exam questions
    @transaction.atomic
    def create_questions(self, request, exam_id):
    
        serializer = QuestionCreateSerializer(data=request.data) 

        if not serializer.is_valid():
            return custom_response(
                data=serializer.errors,
                message="Validation failed",
                success=False,
                status_code=400,
            )

        exam = Exam.objects.get(id=exam_id)

        # Create the ONE question (you are sending only one)
        question = serializer.save(exam=exam)  # This does the job perfectly

        response_data = {
            "exam_id": exam.id,
            "questions_created": 1,
            "total_questions": exam.questions.count(),
            "question_id": question.id,  # nice bonus for you
            "question_text": question.text,
        }

        return custom_response(
            data=response_data,
            message="Question added successfully",
            status_code=201,
        )

    def list(self, request):
        exams = (
            self.get_queryset()
            .only(
                "id",
                "title",
                "duration_minutes",
                "course_id",
                "course__name",
                "course__code",
            )
            .select_related("course")
        )
        print(">>> Exams QuerySet:", exams.query)
        serializer = self.get_serializer_class()(exams, many=True)
        data = {
            "exams": serializer.data,
            "count": exams.count(),
        }
        return custom_response(data=data)

    def retrieve(self, request, exam_id):
        exam = (
            self.get_queryset()
            .only(
                "id",
                "title",
                "duration_minutes",
                "questions__id",
                "questions__text",
                "questions__marks",
                "questions__question_type",
                "questions__choices",
            )
            .get(pk=exam_id)
        )
        if not exam:
            return custom_response(message="exam not found", status_code=404)
        data = {
            "exam": {
                "id": exam.id,
                "title": exam.title,
                "duration_minutes": exam.duration_minutes,
                "questions": QuestionSerializer(exam.questions.all(), many=True).data,
            },
            "count": self.get_queryset().count(),
        }
        return custom_response(data=data)

    @transaction.atomic
    def create(self, request):
        print(">>> Exam Creation Request Data:", request.data)
        try:
            serializer = ExamCreateSerializer(data=request.data)

            if not serializer.is_valid():
                return custom_response(
                    data=serializer.errors,
                    message="Validation failed",
                    success=False,
                    status_code=400,
                )

            # Set the creator to current user
            exam = serializer.save(created_by=request.user)

            print(">>> Exam Created with ID:", exam.id)

            response_data = {
                "exam_id": exam.id,
                "title": exam.title,
                "questions_created": exam.questions.count(),
            }

            print(">>> Exam Creation Response Data:", response_data)

            return custom_response(
                data=response_data, message="Exam created successfully", status_code=201
            )
        except Exception as e:
            # Log the error for debugging
            print(f"Exam creation error: {str(e)}")
            return custom_response(
                message="An error occurred while creating the exam. Please try again.",
                success=False,
                status_code=500
            )

    @action(detail=False, methods=["post"], url_path="bulk-questions")
    def bulk_create_questions(self, request):
    
        serializer = BulkQuestionCreateSerializer(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            return custom_response(
                data=serializer.errors,
                message="Validation failed",
                success=False,
                status_code=400,
            )

        exam_id = serializer.validated_data["exam_id"]
        questions_data = serializer.validated_data["questions"]

        exam = Exam.objects.get(id=exam_id)

        # Bulk create questions
        questions_to_create = [
            Question(exam=exam, **question_data) for question_data in questions_data
        ]

        created_questions = Question.objects.bulk_create(questions_to_create)

        response_data = {
            "exam_id": exam.id,
            "questions_created": len(created_questions),
            "total_questions": exam.questions.count(),
        }

        return custom_response(
            data=response_data,
            message=f"{len(created_questions)} questions added successfully",
            status_code=201,
        )


method_decorator(csrf_exempt, name="dispatch")


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    HIGHLY OPTIMIZED ViewSet for managing user exam submissions
    """

    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return Submission.objects.filter(student=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SubmissionDetailSerializer
        return SubmissionListSerializer

    @transaction.atomic
    def post(self, request):
        """
        OPTIMIZED: Submit exam answers

        Key optimizations:
        1. Bulk operations where possible
        2. select_for_update to prevent race conditions
        3. Efficient question validation
        4. Minimal database queries
        """

        print(">>> Submission Request Data:", request.data)
        serializer = SubmissionCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return custom_response(
                data=serializer.errors,
                message="Validation failed",
                success=False,
                status_code=400,
            )

        exam_id = serializer.validated_data["exam_id"]
        print(">>> Exam ID:", exam_id)
        answers_data = serializer.validated_data["answers"]
        print(">>> Answers Data Type:", type(answers_data))

        print(">>> Answers Data:", answers_data)

        try:
            # Use select_related and only() for efficiency
            exam = (
                Exam.objects.select_related("course")
                .only(
                    "id", "title", "is_active", "start_time", "end_time", "course__name"
                )
                .get(id=exam_id)
            )

        except Exam.DoesNotExist:
            return custom_response(
                message="Exam not found", success=False, status_code=404
            )

        # ✅ NOW validate answer count (after exam is fetched)
        exam_question_count = exam.questions.count()
        print(
            f">>> Exam has {exam_question_count} questions, received {len(answers_data)} answers"
        )

        if len(answers_data) != exam_question_count:
            return custom_response(
                message=f"Number of answers ({len(answers_data)}) does not match number of questions ({exam_question_count})",
                success=False,
                status_code=400,
            )

        # Check if student already submitted (with select_for_update to prevent race)
        existing = (
            Submission.objects.select_for_update()
            .filter(student=request.user, exam=exam)
            .exists()
        )

        if existing:
            return custom_response(
                message="You have already submitted this exam",
                success=False,
                status_code=400,
            )

        print(">>> Validated Answers Data:", answers_data)

        print(
            ">>> Number of Answers Submitted:",
            len(answers_data),
            "for Exam Questions:",
            exam.questions.count(),
        )

        # Create submission
        submission = Submission.objects.create(
            student=request.user,
            exam=exam,
            status="submitted",
            # submitted_at is auto-set by auto_now_add
        )

        # Bulk fetch questions for validation and grading
        question_ids = [ans["question_id"] for ans in answers_data]
        print(">>> Question IDs:", question_ids)
        questions = {
            q.id: q
            for q in Question.objects.filter(id__in=question_ids, exam=exam).only(
                "id", "question_type", "marks", "expected_answer", "text"
            )
        }

        print(">>> Fetched Questions:", questions)

        # Prepare bulk answer creation
        answers_to_create = []
        for answer_data in answers_data:
            question_id = answer_data["question_id"]
            if question_id in questions:
                answers_to_create.append(
                    SubmissionAnswer(
                        submission=submission,
                        question=questions[question_id],
                        answer_text=answer_data["answer_text"],
                    )
                )

        # Bulk create answers
        SubmissionAnswer.objects.bulk_create(answers_to_create)

        # Grade submission
        try:
            self._grade_submission(submission, questions)
        except Exception as e:
            logger.error(f"Grading error for submission {submission.id}: {str(e)}")
            submission.status = "submitted"
            submission.save(update_fields=["status"])

            return custom_response(
                message="Submission saved but grading failed. Please contact support.",
                success=False,
                status_code=500,
            )

        # Refresh and return graded submission
        submission.refresh_from_db()

        # Prepare response data
        response_data = {
            "submission_id": submission.id,
            "exam_title": submission.exam.title,
            "total_score": float(submission.total_score or 0),
            "percentage": float(submission.percentage or 0),
            "passed": submission.passed,
            "status": submission.status,
            "submitted_at": submission.submitted_at,
            "graded_at": submission.graded_at,
        }

        return custom_response(
            data=response_data,
            message="Exam submitted and graded successfully",
            status_code=201,
        )

    def _grade_submission(self, submission: Submission, questions: dict):
        """
        OPTIMIZED: Grade a submission using the grading service

        Key optimizations:
        1. Bulk update instead of individual saves
        2. Single aggregation query for totals
        3. Efficient question prefetching
        """
        submission.status = "grading"
        submission.save(update_fields=["status"])

        # Initialize grader
        grader = GradingService()

        # Fetch answers with related questions efficiently
        answers = list(
            submission.answers.select_related("question").only(
                "id",
                "answer_text",
                "question__id",
                "question__text",
                "question__expected_answer",
                "question__marks",
                "question__question_type",
            )
        )

        # Grade all answers
        answers_to_update = []
        for answer in answers:
            try:
                # Use your KeywordGrader
                # use the id of the question related to this answer to retrieve the question
                question_id = answer.question.id
                question = questions[question_id]
                print(
                    ">>> Grading Question ID:",
                    {"question_id": question_id, "text": question.text},
                )
                awarded_marks, feedback, metadata = grader.grade_answer(
                    question, answer.answer_text
                )
                print(
                    ">>> Graded Marks:",
                    awarded_marks,
                    "Feedback:",
                    feedback,
                    "Metadata:",
                    metadata,
                )
                answer.awarded_marks = Decimal(str(awarded_marks))
                print(">>> Updated Answer Marks:", answer.awarded_marks)
                answers_to_update.append(answer)

                print(
                    ">>> Answer after grading:",
                    {"answer_id": answer.id, "awarded_marks": answer.awarded_marks},
                )

                print("anserds to update:", answers_to_update)

            except Exception as e:
                logger.error(f"Error grading answer {answer.id}: {str(e)}")
                answer.awarded_marks = Decimal("0.00")
                answers_to_update.append(answer)

        # Bulk update answers
        SubmissionAnswer.objects.bulk_update(answers_to_update, ["awarded_marks"])

        # Calculate final results using aggregation (OPTIMIZED)
        result = submission.answers.aggregate(total=Sum("awarded_marks"))
        submission.total_score = result["total"] or Decimal("0.00")

        # Calculate percentage
        exam_total = (
            submission.exam.questions.aggregate(total=Sum("marks"))["total"] or 0
        )
        print(">>> Exam Total Marks:", exam_total)
        print(">>> Submission Total Score:", submission.total_score)
        submission.percentage = (
            (submission.total_score / exam_total * 100)
            if exam_total > 0
            else Decimal("0.00")
        )

        # Determine if passed (assuming 50% is passing)
        submission.passed = submission.percentage >= 50

        # Update status and timestamps
        submission.status = "graded"
        submission.graded_at = timezone.now()

        submission.save(
            update_fields=["total_score", "percentage", "passed", "status", "graded_at"]
        )

    def list(self, request):
        queryset = (
            self.get_queryset()
            .select_related("exam", "exam__course")
            .only(
                "id",
                "status",
                "submitted_at",
                "total_score",
                "percentage",
                "passed",
                "graded_at",
                "feedback",
                "student_id",
                "exam_id",
                "exam__id",
                "exam__title",
                "exam__course_id",
                "exam__course__id",
                "exam__course__name",
                "exam__course__code",
            )
            .order_by("-submitted_at")
        )

        stats = queryset.aggregate(
            total_submissions=Count("id"),
            grand_total_score=Sum("total_score"),
            average_percentage=Avg("percentage"),
            passed_count=Count("id", filter=Q(passed=True)),
            graded_count=Count("id", filter=Q(status="graded")),
        )

        serializer = self.get_serializer(queryset, many=True)

        # Safe stats calculations
        graded_count = stats["graded_count"] or 0

        pass_rate = (
            round((stats["passed_count"] / graded_count) * 100, 2)
            if graded_count > 0
            else 0.0
        )

        # Return with your custom response format
        return custom_response(
            data={
                "submissions": serializer.data,  # ← Now uses SubmissionListSerializer
                "statistics": {
                    "total_submissions": stats["total_submissions"] or 0,
                    "exam_grand_score": float(stats["grand_total_score"] or 0),
                    "average_percentage": round(
                        float(stats["average_percentage"] or 0), 2
                    ),
                    "passed_count": stats["passed_count"] or 0,
                    "graded_count": graded_count,
                    "pass_rate": pass_rate,
                },
            },
            message=(
                "User submissions retrieved successfully"
                if queryset.exists()
                else "No submissions found yet"
            ),
            status_code=200,
        )
    
    def retrieve_submission_answers(self, request, submission_id):
        """
        Retrieve a specific submission with all its answers and question details
        Optimized with select_related and prefetch_related to avoid N+1 queries
        """
        try:
            submission = (
                Submission.objects
                .filter(student=request.user)  # Security: only own submissions
                .select_related('exam', 'exam__course')
                .prefetch_related(
                    Prefetch(
                        'answers',
                        queryset=SubmissionAnswer.objects.select_related('question')
                    )
                )
                .get(pk=submission_id)
            )
        except Submission.DoesNotExist:
            return custom_response(
                message="Submission not found or does not belong to you",
                success=False,
                status_code=404
            )

        # Serialize submission
        submission_data = SubmissionListSerializer(submission).data

        # Build detailed answers
        answers_data = []
        for answer in submission.answers.all():
            answers_data.append({
                "question_id": answer.question.id,
                "question_text": answer.question.text,
                "question_type": answer.question.question_type,
                "your_answer": answer.answer_text,
                "awarded_marks": answer.awarded_marks,
                "max_marks": float(answer.question.marks),
                "feedback": answer.feedback if hasattr(answer, 'feedback') else None,  # if you add it later
            })

        # Optional: total score from answers (in case denormalized total_score is outdated)
        calculated_total = sum(a["awarded_marks"] or 0 for a in answers_data)
        exam_total_marks = sum(a["max_marks"] for a in answers_data)

        response_data = {
            "submission": {
                "id": submission.id,
                "exam_title": submission.exam.title,
                "course_name": submission.exam.course.name,
                "submitted_at": submission.submitted_at,
                "total_score": submission.total_score,
                "percentage": submission.percentage,
                "passed": submission.passed,
                "status": submission.status,
            },
            "answers": answers_data,
            "summary": {
                "calculated_total": calculated_total,
                "exam_total_marks": exam_total_marks,
                "percentage": round((calculated_total / exam_total_marks) * 100, 2) if exam_total_marks > 0 else 0,
            }
        }

        return custom_response(
            data=response_data,
            message="Submission answers retrieved successfully",
            status_code=200
        )