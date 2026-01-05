class BaseGrader:
    """
    Base interface for grading strategies.
    """

    def grade(self, question, student_answer: str) -> float:
        raise NotImplementedError
