from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any
from enum import Enum


class Subject(str, Enum):
    MATH = "math"
    PHYSICS = "physics"
    BIOLOGY = "biology"
    HISTORY = "history"
    CHEMISTRY = "chemistry"
    GENERAL = "general"


class Level(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class StudentQuestion(BaseModel):
    """Input model for student questions"""

    question: str = Field(..., description="The student's question")
    subject: Subject = Field(..., description="The subject domain")
    level: Level = Field(..., description="The difficulty level")
    document_id: Optional[str] = None


class SocraticResponse(BaseModel):
    """Output model for Socratic tutor responses"""

    clarifying_question: str = Field(
        ..., description="A question to guide the student's thinking"
    )
    concept_hint: str = Field(
        ..., description="A helpful hint about the underlying concept"
    )
    feedback: str = Field(..., description="Encouraging feedback for the student")


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str
    message: str


class Document(BaseModel):
    id: str
    filename: str
    content: str
    subject: Subject = Subject.GENERAL
    level: Level = Level.INTERMEDIATE
    created_at: str
    user_id: Optional[str] = None
