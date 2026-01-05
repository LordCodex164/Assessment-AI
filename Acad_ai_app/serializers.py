from .models import Exam, Question, Submission, SubmissionAnswer
from rest_framework import serializers
from course_module.serializers import CourseDetailSerializer
from course_module.models import Course

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "text",
            "marks",
            "question_type",
            "choices",
        ]


class ExamListSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.name", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "course",
            "duration_minutes",
            "course_name",
            "course_code",
        ]


class ExamDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "course",
            "duration_minutes",
            "questions",
        ]


class SubmissionListSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source="exam.title", read_only=True)
    course_name = serializers.CharField(source="exam.course.name", read_only=True)
    course_code = serializers.CharField(source="exam.course.code", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "exam_title",
            "course_name",
            "course_code",
            "status",
            "submitted_at",
            "total_score",
            "percentage",
            "passed",
            "graded_at",
            "feedback",
        ]
        read_only_fields = fields


class SubmissionDetailSerializer(serializers.ModelSerializer):
    """Highly optimized submission detail serializer"""

    exam_title = serializers.CharField(source="exam.title", read_only=True)
    course_name = serializers.CharField(source="exam.course.name", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "exam_title",
            "course_name",
            "status",
            "submitted_at",
            "graded_at",
            "total_score",
            "percentage",
            "passed",
            "feedback",
        ]
        read_only_fields = fields


class AnswerSubmitSerializer(serializers.Serializer):
    """Serializer for answer submission"""

    question_id = serializers.IntegerField()
    answer_text = serializers.CharField(allow_blank=True, trim_whitespace=True)

    def validate_answer_text(self, value):
        # Additional validation if needed
        if len(value) > 10000:
            raise serializers.ValidationError(
                "Answer is too long (max 10000 characters)"
            )
        return value


class SubmissionCreateSerializer(serializers.Serializer):
    """Optimized submission creation serializer"""

    exam_id = serializers.IntegerField()
    answers = AnswerSubmitSerializer(many=True)

    def validate_exam_id(self, value):
        """Validate exam exists and is available"""
        try:
            exam = Exam.objects.only("id", "is_active", "start_time", "end_time").get(
                id=value
            )
            # Add your is_available() check if needed
            if not exam.is_active:
                raise serializers.ValidationError(
                    "This exam is not currently available."
                )
        except Exam.DoesNotExist:
            raise serializers.ValidationError("Exam not found.")
        return value

    def validate(self, data):
        """Validate answers belong to exam"""
        exam = Exam.objects.only("id").get(id=data["exam_id"])
        question_ids = {ans["question_id"] for ans in data["answers"]}

        # Efficient check using exists()
        exam_question_ids = set(
            exam.questions.filter(id__in=question_ids).values_list("id", flat=True)
        )

        if question_ids != exam_question_ids:
            raise serializers.ValidationError(
                "Some questions do not belong to this exam or are invalid."
            )

        return data

class QuestionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating questions"""

    class Meta:
        model = Question
        fields = ["text", "question_type", "expected_answer", "marks"]

    def validate_choices(self, value):
        """Validate choices for MCQ questions"""
        question_type = self.initial_data.get("question_type")
        if question_type == "mcq" and not value:
            raise serializers.ValidationError(
                "Choices are required for multiple choice questions"
            )
        return value


class ExamCreateSerializer(serializers.ModelSerializer):
    questions = QuestionCreateSerializer(many=True, required=False)
    course = serializers.SlugRelatedField(
        slug_field='id',
        queryset=Course.objects.all()
    )

    class Meta:
        model = Exam
        fields = [
            "course",
            "title",
            "duration_minutes",
            "is_active",
            "start_time",
            "end_time",
            "questions",
        ]

    def create(self, validated_data):
        print(">>> Type of course:", type(validated_data.get('course')))
        print(">>> Course value:", validated_data.get('course'))
        print(">>> Full validated_data:", validated_data)
        
        questions_data = validated_data.pop("questions", [])
        
        # This should work if PrimaryKeyRelatedField is working correctly
        exam = Exam.objects.create(**validated_data)

        if questions_data:
            question_objs = [Question(exam=exam, **q) for q in questions_data]
            Question.objects.bulk_create(question_objs)

        return exam

class BulkQuestionCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating questions for an exam"""

    exam_id = serializers.IntegerField()
    questions = QuestionCreateSerializer(many=True)

    def validate_exam_id(self, value):
        try:
            exam = Exam.objects.get(id=value)
            # Check if user is the creator or staff
            request = self.context.get("request")
            if exam.created_by != request.user and not request.user.is_superuser:
                raise serializers.ValidationError(
                    "You can only add questions to exams you created"
                )
        except Exam.DoesNotExist:
            raise serializers.ValidationError("Exam not found")
        return value