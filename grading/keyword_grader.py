import re
from typing import Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from django.core.cache import cache

from Acad_ai_app.models import Question


class GradingService:
    """Mock grading service with multiple algorithms and caching"""
    
    @staticmethod
    def grade_answer(question: Question, answer_text: str) -> Tuple[float, str, Dict]:
        """
        Grade an answer based on question type and criteria
        Returns: (awarded_marks, feedback, metadata)
        """
        # Cache key for similar answer patterns (optional optimization)
        cache_key = f'grade_{question.id}_{hash(answer_text[:100])}'
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        if question.question_type == 'mcq' or question.question_type == 'true_false':
            result = GradingService._grade_mcq(question, answer_text)
        elif question.question_type == 'short':
            result = GradingService._grade_short_answer(question, answer_text)
        elif question.question_type == 'essay':
            result = GradingService._grade_essay(question, answer_text)
        else:
            result = (0, "Unknown question type", {})
        
        # Cache for 1 hour
        cache.set(cache_key, result, timeout=3600)
        return result
    
    @staticmethod
    def _grade_mcq(question: Question, answer_text: str) -> Tuple[float, str, Dict]:
        """Grade multiple choice questions"""
        answer_text = answer_text.strip().lower()
        correct_answer = question.expected_answer.strip().lower()
        
        is_correct = answer_text == correct_answer
        marks = float(question.marks) if is_correct else 0.0
        feedback = "Correct!" if is_correct else f"Incorrect. The correct answer is: {question.correct_answer}"
        
        metadata = {
            'grading_type': 'exact_match',
            'is_correct': is_correct,
            'algorithm': 'string_comparison'
        }

        print("MCQ Grading:", marks, feedback, metadata)
        
        return marks, feedback, metadata
    
    @staticmethod
    @staticmethod
    def _grade_essay(question: Question, answer_text: str) -> Tuple[float, str, Dict]:
        """Grade essay using advanced criteria"""
        if not answer_text.strip():
            return 0.0, "No answer provided", {'grading_type': 'empty'}
        
        word_count = len(answer_text.split())
        print("Essay Word Count:", word_count)
        
        # Word count penalty
        word_count_score = 1.0
        word_count_feedback = ""
        if question.min_word_count and word_count < question.min_word_count:
            word_count_score = max(0.5, word_count / question.min_word_count)
            word_count_feedback = f"Answer is below minimum word count ({word_count}/{question.min_word_count})"
        
        # Keyword coverage
        keyword_score = 0.0
        keywords_found = []
        has_keywords = question.keywords and isinstance(question.keywords, list) and len(question.keywords) > 0
        
        if has_keywords:
            keyword_score, keywords_found = GradingService._calculate_keyword_score(
                answer_text, 
                question.keywords
            )
        
        # Content similarity
        similarity_score = 0.0
        has_expected_answer = question.expected_answer and question.expected_answer.strip()
        
        if has_expected_answer:
            similarity_score = GradingService._calculate_similarity(
                answer_text, 
                question.expected_answer
            )
        
        # ✅ DYNAMIC WEIGHTS: Adjust based on what's available
        if has_keywords and has_expected_answer:
            # All criteria available: 40% keywords, 40% similarity, 20% word count
            combined_score = (
                keyword_score * 0.4 + 
                similarity_score * 0.4 + 
                word_count_score * 0.2
            )
        elif has_keywords and not has_expected_answer:
            # Only keywords: 70% keywords, 30% word count
            combined_score = (
                keyword_score * 0.7 + 
                word_count_score * 0.3
            )
        elif not has_keywords and has_expected_answer:
            # Only similarity: 80% similarity, 20% word count
            combined_score = (
                similarity_score * 0.8 + 
                word_count_score * 0.2
            )
        else:
            # Only word count (fallback)
            combined_score = word_count_score
        
        awarded_marks = round(float(question.marks) * combined_score, 2)
        
        # Generate detailed feedback
        feedback_parts = []
        if word_count_feedback:
            feedback_parts.append(word_count_feedback)
        
        if has_keywords and keyword_score < 0.5:
            missing_count = len(question.keywords) - len(keywords_found)
            feedback_parts.append(f"Consider including {missing_count} more key concepts")
        
        if has_expected_answer:
            if similarity_score > 0.7:
                feedback_parts.append("Excellent coverage of expected content")
            elif similarity_score > 0.4:
                feedback_parts.append("Good partial coverage of expected content")
            else:
                feedback_parts.append("Answer could be more aligned with expected response")
        
        feedback = ". ".join(feedback_parts) if feedback_parts else "Good answer"
        
        metadata = {
            'grading_type': 'essay',
            'word_count': word_count,
            'word_count_score': round(word_count_score, 3),
            'keyword_score': round(keyword_score, 3),
            'similarity_score': round(similarity_score, 3),
            'combined_score': round(combined_score, 3),
            'keywords_found': keywords_found,
            'has_keywords': has_keywords,
            'has_expected_answer': has_expected_answer,
            'algorithm': 'multi_factor_analysis_adaptive'
        }
        
        print("Essay Grading:", awarded_marks, feedback, metadata)
        
        return awarded_marks, feedback, metadata
        
    
    @staticmethod
    def _calculate_keyword_score(answer_text: str, keywords: list) -> Tuple[float, list]:
        """Calculate score based on keyword density - returns score and found keywords"""
        if not keywords:
            return 0.5, []
        
        answer_lower = answer_text.lower()
        found_keywords = [kw for kw in keywords if kw.lower() in answer_lower]
        score = len(found_keywords) / len(keywords)
        return score, found_keywords
    
    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts using TF-IDF"""
        if not text1.strip() or not text2.strip():
            return 0.0
        
        try:
            vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=1000,
                ngram_range=(1, 2)
            )
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            # Fallback to simple word overlap
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            if not words1 or not words2:
                return 0.0
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def _generate_feedback(combined_score: float, keyword_score: float, 
                          similarity_score: float, keywords_found: list) -> str:
        """Generate human-readable feedback"""
        if combined_score >= 0.8:
            return f"Excellent answer! You covered {len(keywords_found)} key concepts effectively."
        elif combined_score >= 0.6:
            return "Good answer with room for improvement in detail or accuracy."
        elif combined_score >= 0.4:
            return "Partial answer. Consider reviewing the key concepts and providing more detail."
        else:
            return "Answer needs significant improvement. Review the material carefully and ensure you address the key points."