"""
DSPy Optimizers for Socratic AI Tutor

This module provides optimization capabilities using DSPy's MIPROv2 and BootstrapFewShot.
"""

import os
import logging
import json
from typing import List, Dict, Any
import dspy
from pathlib import Path
from app.dspy_modules import SocraticTutor, SocraticTutorModule

# Configure logging
logger = logging.getLogger(__name__)


class OptimizationMetrics:
    """Custom metrics for evaluating Socratic responses"""

    @staticmethod
    def socratic_quality_metric(example, prediction, trace=None):
        """
        Evaluate the quality of Socratic tutoring responses

        This metric scores responses based on three criteria:
        1. Clarity - How clear and thoughtful is the clarifying question
        2. Hint quality - Does the hint guide without giving away answers
        3. Level appropriateness - Is the response appropriate for the student level

        Args:
            example: The input example with question, subject, level
            prediction: The model's prediction with clarifying_question, concept_hint, feedback
            trace: Optional trace object for storing detailed metrics

        Returns:
            Float score between 0 and 1
        """
        # Check if the prediction has the expected fields
        if not hasattr(prediction, "clarifying_question") or not hasattr(
            prediction, "concept_hint"
        ):
            logger.warning("Prediction missing required fields")
            return 0.0

        # Extract the prediction fields
        clarifying_question = prediction.clarifying_question
        concept_hint = prediction.concept_hint
        feedback = prediction.feedback if hasattr(prediction, "feedback") else ""

        # Simple length-based heuristics (could be replaced with more sophisticated metrics)
        clarity_score = min(
            1.0, len(clarifying_question.split()) / 20
        )  # Aim for reasonably detailed questions
        hint_score = min(
            1.0, len(concept_hint.split()) / 30
        )  # Encourage detailed hints

        # Check if question actually ends with a question mark
        if clarifying_question and clarifying_question.strip().endswith("?"):
            clarity_score += 0.2
            clarity_score = min(1.0, clarity_score)

        # Penalize direct answers in the hint
        direct_answer_phrases = [
            "the answer is",
            "the solution is",
            "you should",
            "you need to",
        ]
        for phrase in direct_answer_phrases:
            if phrase in concept_hint.lower():
                hint_score *= 0.7

        # Basic level appropriateness check
        level = example.level if hasattr(example, "level") else "intermediate"
        level_score = 0.7  # Default assumption

        # Store scores in trace if provided
        if trace is not None:
            trace["clarity_score"] = clarity_score
            trace["hint_score"] = hint_score
            trace["level_score"] = level_score

        # Compute weighted score
        weights = {"clarity": 0.4, "hint": 0.4, "level": 0.2}
        total_score = (
            weights["clarity"] * clarity_score
            + weights["hint"] * hint_score
            + weights["level"] * level_score
        )

        return total_score


class PromptOptimizer:
    """Class for optimizing DSPy prompts"""

    def __init__(self, trainset_path=None, devset_path=None):
        """
        Initialize the prompt optimizer

        Args:
            trainset_path: Path to JSON file with training examples
            devset_path: Path to JSON file with validation examples
        """
        self.trainset = []
        self.devset = []

        # Load datasets if paths provided
        if trainset_path and os.path.exists(trainset_path):
            self.trainset = self._load_examples(trainset_path)
            logger.info(f"Loaded {len(self.trainset)} training examples")

        if devset_path and os.path.exists(devset_path):
            self.devset = self._load_examples(devset_path)
            logger.info(f"Loaded {len(self.devset)} validation examples")

    def _load_examples(self, file_path):
        """Load examples from a JSON file"""
        examples = []
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

                for item in data:
                    # Create a DSPy example
                    example = dspy.Example(
                        question=item.get("question", ""),
                        subject=item.get("subject", "general"),
                        level=item.get("level", "beginner"),
                        reference_response=item.get("reference_response", {}),
                    ).with_inputs("question", "subject", "level")

                    examples.append(example)
        except Exception as e:
            logger.error(f"Error loading examples from {file_path}: {str(e)}")

        return examples

    def optimize_with_mipro(self, lm=None, module=None):
        """
        Optimize prompts using MIPROv2

        Args:
            lm: DSPy language model to use
            module: DSPy module to optimize (defaults to SocraticTutorModule)

        Returns:
            Optimized DSPy module
        """
        # Use provided LM or default to the configured one
        lm = lm or dspy.settings.lm
        if not lm:
            logger.error("No language model provided or configured")
            return None

        # Configure DSPy with the LM
        dspy.configure(lm=lm)

        # Use provided module or create a default one
        module = module or SocraticTutorModule()

        # Check if we have training data
        if not self.trainset:
            logger.error("No training examples available for optimization")
            return module

        try:
            logger.info("Starting MIPROv2 optimization")

            # Create the MIPROv2 optimizer
            mipro = dspy.MIPROv2(
                metric=OptimizationMetrics.socratic_quality_metric,
                max_bootstrapped_demos=5,
                max_labeled_demos=10,
                num_threads=4,
                max_rounds=3,
                max_errors=100,
            )

            # Run optimization
            optimized_module = mipro.compile(
                module,
                trainset=self.trainset,
                devset=self.devset
                or self.trainset[:3],  # Use a subset of training data if no devset
            )

            logger.info("MIPROv2 optimization completed successfully")
            return optimized_module

        except Exception as e:
            logger.error(f"Error during MIPROv2 optimization: {str(e)}")
            return module

    def optimize_with_bootstrap(self, lm=None, module=None):
        """
        Optimize prompts using BootstrapFewShot

        Args:
            lm: DSPy language model to use
            module: DSPy module to optimize (defaults to SocraticTutorModule)

        Returns:
            Optimized DSPy module
        """
        # Use provided LM or default to the configured one
        lm = lm or dspy.settings.lm
        if not lm:
            logger.error("No language model provided or configured")
            return None

        # Configure DSPy with the LM
        dspy.configure(lm=lm)

        # Use provided module or create a default one
        module = module or SocraticTutorModule()

        # Check if we have training data
        if not self.trainset:
            logger.error("No training examples available for optimization")
            return module

        try:
            logger.info("Starting BootstrapFewShot optimization")

            # Create the BootstrapFewShot optimizer
            bootstrap = dspy.BootstrapFewShot(
                metric=OptimizationMetrics.socratic_quality_metric,
                max_bootstrapped_demos=5,
                num_threads=4,
            )

            # Run optimization
            optimized_module = bootstrap.compile(module, trainset=self.trainset)

            logger.info("BootstrapFewShot optimization completed successfully")
            return optimized_module

        except Exception as e:
            logger.error(f"Error during BootstrapFewShot optimization: {str(e)}")
            return module


class OptimizedTutorService:
    """Service that uses optimized DSPy modules"""

    def __init__(
        self, openai_model: str = "gpt-4o", optimization_method: str = "mipro"
    ):
        """
        Initialize the service with optimization

        Args:
            openai_model: OpenAI model to use
            optimization_method: Optimization method ("mipro" or "bootstrap")
        """
        from app.dspy_modules import SocraticTutorService

        # Create the base service
        self.base_service = SocraticTutorService(openai_model)
        self.lm = self.base_service.lm

        # Create the optimizer
        trainset_path = os.path.join(os.path.dirname(__file__), "../data/trainset.json")
        devset_path = os.path.join(os.path.dirname(__file__), "../data/devset.json")

        self.optimizer = PromptOptimizer(
            trainset_path=trainset_path if os.path.exists(trainset_path) else None,
            devset_path=devset_path if os.path.exists(devset_path) else None,
        )

        # Create optimized module
        self.optimized_module = None
        self.optimization_method = optimization_method

    def get_socratic_response(
        self, question: str, subject: str, level: str
    ) -> Dict[str, str]:
        """
        Get an optimized Socratic response

        Args:
            question: The student's question
            subject: The subject domain
            level: The difficulty level

        Returns:
            Dictionary with clarifying_question, concept_hint, and feedback
        """
        try:
            # Initialize optimized module if needed
            if self.optimized_module is None:
                logger.info(f"Optimizing tutor module with {self.optimization_method}")

                # Configure DSPy with our LM
                dspy.configure(lm=self.lm)

                # Run optimization based on selected method
                if self.optimization_method == "mipro":
                    self.optimized_module = self.optimizer.optimize_with_mipro(
                        lm=self.lm, module=SocraticTutorModule()
                    )
                else:
                    self.optimized_module = self.optimizer.optimize_with_bootstrap(
                        lm=self.lm, module=SocraticTutorModule()
                    )

                # Fall back to base module if optimization failed
                if self.optimized_module is None:
                    logger.warning("Optimization failed, using base module")
                    self.optimized_module = SocraticTutorModule()

            # Always reconfigure DSPy
            dspy.configure(lm=self.lm)

            # Get prediction from optimized module
            try:
                # Convert subject and level to strings
                subject_str = (
                    subject.value if hasattr(subject, "value") else str(subject)
                )
                level_str = level.value if hasattr(level, "value") else str(level)

                # Make prediction
                prediction = self.optimized_module.forward(
                    question=question, subject=subject_str, level=level_str
                )

                logger.info("Optimized prediction successful")

                return {
                    "clarifying_question": prediction.clarifying_question,
                    "concept_hint": prediction.concept_hint,
                    "feedback": prediction.feedback,
                }

            except Exception as e:
                # Log the error and fall back to the base service
                logger.error(f"Optimized prediction failed: {str(e)}")
                return self.base_service.get_socratic_response(question, subject, level)

        except Exception as e:
            # Log the error and fall back to the base service
            logger.error(f"Error in optimized service: {str(e)}")
            return self.base_service.get_socratic_response(question, subject, level)
