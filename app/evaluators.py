"""
DSPy Evaluators for Socratic AI Tutor

This module will contain evaluators to assess the quality of Socratic responses.
Future implementations will include:
- Clarity evaluator
- Helpfulness evaluator
- Subject accuracy evaluator
- Level appropriateness evaluator
"""

import dspy
from typing import Dict, Any


class SocraticResponseEvaluator(dspy.Signature):
    """Evaluate the quality of a Socratic tutor response"""

    question: str = dspy.InputField(desc="The original student question")
    subject: str = dspy.InputField(desc="The subject domain")
    level: str = dspy.InputField(desc="The difficulty level")
    clarifying_question: str = dspy.InputField(desc="The AI's clarifying question")
    concept_hint: str = dspy.InputField(desc="The AI's concept hint")
    feedback: str = dspy.InputField(desc="The AI's feedback")

    clarity_score: float = dspy.OutputField(desc="Clarity score (0-1)")
    helpfulness_score: float = dspy.OutputField(desc="Helpfulness score (0-1)")
    appropriateness_score: float = dspy.OutputField(
        desc="Level appropriateness score (0-1)"
    )


# TODO: Implement evaluator classes
# class ClarityEvaluator(dspy.Module):
#     """Evaluates clarity of responses"""
#     pass

# class HelpfulnessEvaluator(dspy.Module):
#     """Evaluates helpfulness of responses"""
#     pass

# class SubjectAccuracyEvaluator(dspy.Module):
#     """Evaluates subject-specific accuracy"""
#     pass
