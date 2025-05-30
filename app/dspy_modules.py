import dspy
from typing import Literal
import logging
import os
import requests
from app.models import Subject, Level

# Configure logging
logger = logging.getLogger(__name__)


class SocraticTutor(dspy.Signature):
    """Respond to students with a clarifying question and helpful hints."""

    question: str = dspy.InputField(desc="The student's question")
    subject: str = dspy.InputField(
        desc="The subject domain (math, physics, biology, history, chemistry)"
    )
    level: str = dspy.InputField(
        desc="The difficulty level (beginner, intermediate, advanced)"
    )

    clarifying_question: str = dspy.OutputField(
        desc="A thoughtful question to guide the student's thinking and prompt deeper consideration of the topic"
    )
    concept_hint: str = dspy.OutputField(
        desc="A subtle hint that points toward relevant concepts without revealing answers. Focus on suggesting what to think about rather than explaining. Use Socratic questioning to guide rather than direct explanation."
    )
    feedback: str = dspy.OutputField(
        desc="Encouraging and supportive feedback for the student"
    )


class SocraticTutorModule(dspy.Module):
    """Main DSPy module for Socratic tutoring"""

    def __init__(self):
        super().__init__()
        # Use ChainOfThought instead of Predict for better reasoning
        self.tutor = dspy.ChainOfThought(SocraticTutor)

    def forward(self, question: str, subject: str, level: str):
        """
        Process a student question and return Socratic-style guidance

        Args:
            question: The student's question
            subject: The subject domain
            level: The difficulty level

        Returns:
            DSPy prediction with clarifying_question, concept_hint, and feedback
        """
        # Create the prediction
        prediction = self.tutor(question=question, subject=subject, level=level)

        return prediction


class SocraticTutorService:
    """Service class to handle DSPy module initialization and predictions"""

    def __init__(self, openai_model: str = "gpt-4o"):
        """Initialize the service with OpenAI model, defaulting to GPT-4o"""
        try:
            # Get OpenAI API key from environment
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")

            # Clean the API key - remove any whitespace, newlines, etc.
            api_key = api_key.strip()

            logger.info(f"Initializing DSPy with OpenAI model: {openai_model}")
            logger.info(f"API key present: {bool(api_key and len(api_key) > 10)}")

            # First verify the OpenAI API key works with a direct API call
            self._test_openai_direct_connection(api_key)

            # Use the specified model, ensuring it's a valid OpenAI model name
            # Default to gpt-4o if no specific model is provided
            model_name = openai_model if openai_model else "gpt-4o"
            logger.info(f"Using model: {model_name}")

            # Initialize DSPy LM with the correct model format
            try:
                logger.info("Initializing DSPy LM...")
                # Use the correct format for OpenAI models in DSPy
                model_name = "gpt-4o"  # Hard-code to a known working model
                logger.info(f"Using model: {model_name}")

                self.lm = dspy.LM(
                    model=model_name,  # Just use the model name directly - "gpt-4o"
                    api_key=api_key,
                    api_base="https://api.openai.com/v1",  # Explicitly set the API base URL
                    max_tokens=1000,
                    temperature=0.0,
                    num_retries=3,
                    cache=True,  # Enable caching for improved performance
                )
                logger.info("DSPy LM initialization successful")
            except Exception as e:
                logger.error(f"Failed to initialize DSPy LM: {str(e)}")
                raise ValueError(f"Failed to initialize DSPy language model: {str(e)}")

            # Configure DSPy globally with this LM
            if self.lm:
                dspy.configure(lm=self.lm)
                logger.info("DSPy LM configuration successful")

                # Test with a very simple prompt
                try:
                    test_result = self.lm("Testing DSPy connection", max_tokens=5)
                    logger.info(f"DSPy test successful: {test_result}")
                except Exception as test_err:
                    logger.warning(
                        f"DSPy test call failed, but continuing: {str(test_err)}"
                    )
            else:
                raise ValueError("Failed to initialize DSPy language model")

            # Initialize the tutor module
            self.tutor_module = SocraticTutorModule()
            logger.info("SocraticTutorModule initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize SocraticTutorService: {str(e)}")
            raise

    def _test_openai_direct_connection(self, api_key):
        """Test direct OpenAI connection to verify API key and connectivity"""
        try:
            # Clean the API key again to be safe
            api_key = api_key.strip()

            # Simple test request to OpenAI API
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Say test"}],
                "max_tokens": 5,
            }
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10,
            )
            if response.status_code == 200:
                logger.info("Direct OpenAI API connection test successful")
            else:
                logger.warning(
                    f"OpenAI API test returned status {response.status_code}: {response.text}"
                )
        except Exception as e:
            logger.warning(f"Direct OpenAI API test failed: {str(e)}")

    def get_socratic_response(
        self, question: str, subject: Subject, level: Level
    ) -> dict:
        """
        Get a Socratic response for a student question

        Args:
            question: The student's question
            subject: The subject domain
            level: The difficulty level

        Returns:
            Dictionary with clarifying_question, concept_hint, and feedback
        """
        try:
            # Convert enums to strings for DSPy
            subject_str = subject.value
            level_str = level.value

            logger.info(f"Making DSPy prediction for question: {question[:50]}...")
            logger.info(f"Subject: {subject_str}, Level: {level_str}")

            # Always reconfigure DSPy in Docker environments (addresses persistence issues)
            dspy.configure(lm=self.lm)
            logger.info("DSPy LM is properly configured, making prediction...")

            # Get prediction from DSPy module - wrap in try/except for better error handling
            try:
                prediction = self.tutor_module.forward(
                    question=question, subject=subject_str, level=level_str
                )

                logger.info("DSPy prediction successful")
                logger.info(
                    f"Prediction result: clarifying_question='{prediction.clarifying_question[:50]}...', concept_hint='{prediction.concept_hint[:50]}...', feedback='{prediction.feedback[:50]}...'"
                )

                return {
                    "clarifying_question": prediction.clarifying_question,
                    "concept_hint": prediction.concept_hint,
                    "feedback": prediction.feedback,
                }
            except Exception as inner_e:
                # Log the specific prediction error
                logger.error(f"DSPy prediction execution failed: {str(inner_e)}")
                # Try one more time with a simple direct LM call
                try:
                    logger.info("Attempting direct LM call as fallback...")
                    # Simple prompt as fallback
                    fallback_prompt = f"""
                    You are a Socratic tutor helping a {level_str} student with a {subject_str} question: "{question}"
                    
                    Provide:
                    1. A clarifying question to guide their thinking and prompt deeper consideration
                    2. A subtle hint about relevant concepts - do NOT explain the answer directly, only suggest what to think about through Socratic questioning
                    3. Encouraging feedback
                    
                    Format as JSON with keys: clarifying_question, concept_hint, feedback
                    """
                    direct_response = self.lm(fallback_prompt)
                    logger.info(
                        f"Direct LM call successful: {direct_response[:100]}..."
                    )
                    # Re-raise the original error so we use the fallback response below
                    raise inner_e
                except Exception as fallback_e:
                    logger.error(f"Even direct LM call failed: {str(fallback_e)}")
                    raise inner_e
        except Exception as e:
            # Log the actual error
            logger.error(f"DSPy prediction failed with error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")

            # Fallback response in case of errors
            return {
                "clarifying_question": "What specific aspect of this topic would you like to explore further?",
                "concept_hint": f"This is a great {subject_str} question at the {level_str} level. Let's break it down step by step.",
                "feedback": "I appreciate your curiosity! Let's work through this together.",
            }


class EnsembleTutorModule(dspy.Module):
    """Enhanced DSPy module that generates multiple responses and selects the best one"""

    def __init__(self, num_responses=3):
        super().__init__()
        self.tutor = dspy.ChainOfThought(SocraticTutor)
        self.num_responses = num_responses

    def forward(self, question: str, subject: str, level: str):
        """
        Process a student question, generate multiple responses, and select the best one

        Args:
            question: The student's question
            subject: The subject domain
            level: The difficulty level

        Returns:
            The best DSPy prediction with clarifying_question, concept_hint, and feedback
        """
        # Generate multiple responses with different temperatures
        predictions = []

        # Use different temperature settings to get diverse responses
        temperatures = [0.0, 0.3, 0.7][: self.num_responses]
        if len(temperatures) < self.num_responses:
            temperatures.extend([0.5] * (self.num_responses - len(temperatures)))

        for temp in temperatures:
            # Configure temperature for this prediction
            prev_temp = None
            if hasattr(dspy.settings, "lm") and dspy.settings.lm is not None:
                prev_temp = dspy.settings.lm.temperature
                dspy.settings.lm.temperature = temp

            # Generate prediction
            try:
                pred = self.tutor(question=question, subject=subject, level=level)
                predictions.append(pred)
            except Exception as e:
                logger.error(
                    f"Error generating prediction with temperature {temp}: {str(e)}"
                )

            # Restore previous temperature
            if prev_temp is not None:
                dspy.settings.lm.temperature = prev_temp

        # If we failed to generate any predictions, fall back to a single prediction
        if not predictions:
            return self.tutor(question=question, subject=subject, level=level)

        # Select the best prediction based on quality criteria
        best_pred = self.select_best_prediction(predictions, question)
        return best_pred

    def select_best_prediction(self, predictions, question):
        """
        Select the best prediction from multiple candidates

        Currently uses a simple heuristic based on response length and specificity.
        This could be enhanced with more sophisticated metrics in the future.

        Args:
            predictions: List of DSPy predictions
            question: The original question for context

        Returns:
            The best prediction
        """
        if not predictions:
            return None

        # If only one prediction, return it
        if len(predictions) == 1:
            return predictions[0]

        # Define scoring weights
        weights = {
            "question_score": 0.4,  # How good is the clarifying question
            "hint_score": 0.4,  # How good is the concept hint
            "feedback_score": 0.2,  # How good is the feedback
        }

        scores = []
        for pred in predictions:
            # Score the clarifying question (higher score for longer, more detailed questions)
            question_len = len(pred.clarifying_question.split())
            question_specificity = len(
                set(pred.clarifying_question.lower().split())
                & set(question.lower().split())
            ) / max(1, len(question.split()))
            question_score = min(
                1.0, (question_len / 20) * 0.7 + question_specificity * 0.3
            )

            # Score the concept hint (higher score for more detailed hints)
            hint_len = len(pred.concept_hint.split())
            hint_score = min(1.0, hint_len / 30)

            # Score the feedback (higher score for more personalized feedback)
            feedback_len = len(pred.feedback.split())
            feedback_score = min(1.0, feedback_len / 25)

            # Calculate weighted score
            total_score = (
                weights["question_score"] * question_score
                + weights["hint_score"] * hint_score
                + weights["feedback_score"] * feedback_score
            )

            scores.append(total_score)

        # Return the prediction with the highest score
        best_index = scores.index(max(scores))
        return predictions[best_index]


class EnsembleTutorService:
    """Service class that uses the ensemble tutor module"""

    def __init__(self, openai_model: str = "gpt-4o"):
        """Initialize the service with the standard tutor service"""
        # Create the base service with the proper LM initialization
        self.base_service = SocraticTutorService(openai_model)
        self.ensemble_module = None
        self.lm = self.base_service.lm  # Use the LM from the base service

    def get_socratic_response(
        self, question: str, subject: Subject, level: Level
    ) -> dict:
        """
        Get an ensemble Socratic response for a student question

        Args:
            question: The student's question
            subject: The subject domain
            level: The difficulty level

        Returns:
            Dictionary with clarifying_question, concept_hint, and feedback
        """
        try:
            # Initialize the ensemble module if needed
            if self.ensemble_module is None:
                # Configure DSPy with the LM from the base service
                dspy.configure(lm=self.lm)
                self.ensemble_module = EnsembleTutorModule(num_responses=3)

            # Convert enums to strings for DSPy
            subject_str = subject.value
            level_str = level.value

            logger.info(f"Making ensemble prediction for question: {question[:50]}...")

            # Always reconfigure DSPy in Docker environments (addresses persistence issues)
            dspy.configure(lm=self.lm)

            # Get prediction from the ensemble module
            try:
                prediction = self.ensemble_module.forward(
                    question=question, subject=subject_str, level=level_str
                )

                logger.info("Ensemble prediction successful")

                return {
                    "clarifying_question": prediction.clarifying_question,
                    "concept_hint": prediction.concept_hint,
                    "feedback": prediction.feedback,
                }
            except Exception as e:
                # Log the error and fall back to the base service
                logger.error(f"Ensemble prediction failed: {str(e)}")
                return self.base_service.get_socratic_response(question, subject, level)

        except Exception as e:
            # Log the error and fall back to the base service
            logger.error(f"Error in ensemble service: {str(e)}")
            return self.base_service.get_socratic_response(question, subject, level)


class MathTutorModule(dspy.Module):
    """Specialized DSPy module for mathematics using ProgramOfThought"""

    def __init__(self):
        super().__init__()
        # For math, we use ProgramOfThought which can solve problems step-by-step
        # and even generate code for calculations when needed
        self.tutor = dspy.ProgramOfThought(SocraticTutor)

    def forward(self, question: str, subject: str, level: str):
        """Process a math question and return Socratic-style guidance"""
        return self.tutor(question=question, subject=subject, level=level)


class ScienceTutorModule(dspy.Module):
    """Specialized DSPy module for science subjects using ChainOfThought"""

    def __init__(self):
        super().__init__()
        # For science, we use ChainOfThought to break down complex concepts
        self.tutor = dspy.ChainOfThought(SocraticTutor)

    def forward(self, question: str, subject: str, level: str):
        """Process a science question and return Socratic-style guidance"""
        return self.tutor(question=question, subject=subject, level=level)


class HumanitiesTutorModule(dspy.Module):
    """Specialized DSPy module for humanities subjects using Predict"""

    def __init__(self):
        super().__init__()
        # For humanities, a basic Predict is often sufficient
        self.tutor = dspy.Predict(SocraticTutor)

    def forward(self, question: str, subject: str, level: str):
        """Process a humanities question and return Socratic-style guidance"""
        return self.tutor(question=question, subject=subject, level=level)


class SpecialistTutorService:
    """Service that routes questions to subject-specific specialist tutors"""

    def __init__(self, openai_model: str = "gpt-4o"):
        """Initialize the service with specialized tutors for different subjects"""
        # Create the base service with the proper LM initialization
        self.base_service = SocraticTutorService(openai_model)
        self.specialists = {}
        self.lm = self.base_service.lm  # Use the LM from the base service

    def _get_specialist_for_subject(self, subject: Subject):
        """Get or create the appropriate specialist for a given subject"""
        subject_str = subject.value

        # Return existing specialist if already created
        if subject_str in self.specialists:
            return self.specialists[subject_str]

        # Configure DSPy with our language model
        dspy.configure(lm=self.lm)

        # Create the appropriate specialist based on subject
        if subject_str in ["math"]:
            specialist = MathTutorModule()
        elif subject_str in ["physics", "biology", "chemistry"]:
            specialist = ScienceTutorModule()
        else:  # history and other humanities
            specialist = HumanitiesTutorModule()

        # Cache the specialist for future use
        self.specialists[subject_str] = specialist
        return specialist

    def get_socratic_response(
        self, question: str, subject: Subject, level: Level
    ) -> dict:
        """
        Route the question to the appropriate subject specialist

        Args:
            question: The student's question
            subject: The subject domain
            level: The difficulty level

        Returns:
            Dictionary with clarifying_question, concept_hint, and feedback
        """
        try:
            # Get the appropriate specialist for this subject
            specialist = self._get_specialist_for_subject(subject)

            # Convert enums to strings for DSPy
            subject_str = subject.value
            level_str = level.value

            logger.info(f"Using specialist for {subject_str}: {question[:50]}...")

            # Always reconfigure DSPy in Docker environments (addresses persistence issues)
            dspy.configure(lm=self.lm)

            # Get prediction from the specialist
            try:
                prediction = specialist.forward(
                    question=question, subject=subject_str, level=level_str
                )

                logger.info(f"Specialist prediction for {subject_str} successful")

                return {
                    "clarifying_question": prediction.clarifying_question,
                    "concept_hint": prediction.concept_hint,
                    "feedback": prediction.feedback,
                }
            except Exception as e:
                # Log the error and fall back to the base service
                logger.error(f"Specialist prediction failed: {str(e)}")
                return self.base_service.get_socratic_response(question, subject, level)

        except Exception as e:
            # Log the error and fall back to the base service
            logger.error(f"Error in specialist service: {str(e)}")
            return self.base_service.get_socratic_response(question, subject, level)


# Combined service that uses both ensemble and specialist approaches
class AdvancedTutorService:
    """Combined service that uses both ensemble and specialist approaches"""

    def __init__(self, openai_model: str = "gpt-4o"):
        """Initialize with both ensemble and specialist services"""
        # Create the base service with the proper LM initialization
        self.base_service = SocraticTutorService(openai_model)

        # Create the ensemble and specialist services, sharing the same LM
        self.ensemble_service = EnsembleTutorService(openai_model)
        self.specialist_service = SpecialistTutorService(openai_model)

        # Ensure all services use the same LM instance
        self.lm = self.base_service.lm
        self.ensemble_service.lm = self.lm
        self.specialist_service.lm = self.lm

    def get_socratic_response(
        self, question: str, subject: Subject, level: Level
    ) -> dict:
        """
        Get the best response using both specialist and ensemble approaches

        For math and science questions, prioritize the specialist approach.
        For other subjects, use the ensemble approach.

        Args:
            question: The student's question
            subject: The subject domain
            level: The difficulty level

        Returns:
            Dictionary with clarifying_question, concept_hint, and feedback
        """
        try:
            # Determine which approach to use based on subject
            subject_str = subject.value

            if subject_str in ["math", "physics", "chemistry", "biology"]:
                # For STEM subjects, use the specialist approach
                logger.info(f"Using specialist approach for {subject_str}")
                return self.specialist_service.get_socratic_response(
                    question, subject, level
                )
            else:
                # For humanities, use the ensemble approach
                logger.info(f"Using ensemble approach for {subject_str}")
                return self.ensemble_service.get_socratic_response(
                    question, subject, level
                )

        except Exception as e:
            # Log the error and fall back to the base service
            logger.error(f"Error in advanced service: {str(e)}")
            return self.base_service.get_socratic_response(question, subject, level)
