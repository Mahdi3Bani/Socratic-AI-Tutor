"""
Retrieval Augmented Generation (RAG) module for Socratic AI Tutor

This module enhances the tutor with knowledge retrieval from uploaded documents.
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional
import dspy
from pathlib import Path
from app.dspy_modules import SocraticTutor
from app.document_service import DocumentService
from app.models import Document

# Configure logging
logger = logging.getLogger(__name__)


class KnowledgePassage:
    """Represents a passage of domain knowledge."""

    def __init__(self, text: str, subject: str, level: str, source: str = None):
        self.text = text
        self.subject = subject
        self.level = level
        self.source = source

    def __str__(self):
        return f"[{self.subject.upper()} - {self.level}] {self.text[:100]}..."


class DocumentBasedRetriever:
    """Retriever that can work with both static knowledge and uploaded documents."""

    def __init__(
        self, knowledge_path: str = None, document_service: DocumentService = None
    ):
        """Initialize with paths to knowledge files and document service."""
        self.passages = []
        self.embeddings = None
        self.knowledge_path = knowledge_path or os.path.join(
            os.path.dirname(__file__), "../knowledge"
        )
        self.document_service = document_service or DocumentService()

        # Load static knowledge if path exists
        if os.path.exists(self.knowledge_path):
            self._load_knowledge()
        else:
            logger.warning(f"Knowledge path not found: {self.knowledge_path}")

    def _load_knowledge(self):
        """Load knowledge from JSON files in the knowledge directory."""
        try:
            for file_path in Path(self.knowledge_path).glob("*.json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # Process each entry in the knowledge file
                    for entry in data.get("entries", []):
                        self.passages.append(
                            KnowledgePassage(
                                text=entry.get("text", ""),
                                subject=entry.get("subject", "general"),
                                level=entry.get("level", "beginner"),
                                source=entry.get("source", file_path.name),
                            )
                        )

            logger.info(f"Loaded {len(self.passages)} static knowledge passages")
        except Exception as e:
            logger.error(f"Error loading knowledge: {str(e)}")

    def _document_to_passages(self, document: Document) -> List[KnowledgePassage]:
        """Convert a document to a list of knowledge passages by chunking the content."""
        passages = []

        # Simple chunking by paragraphs
        paragraphs = document.content.split("\n\n")

        for i, paragraph in enumerate(paragraphs):
            # Skip empty paragraphs
            if not paragraph.strip():
                continue

            passages.append(
                KnowledgePassage(
                    text=paragraph,
                    subject=(
                        document.subject.value
                        if hasattr(document.subject, "value")
                        else document.subject
                    ),
                    level=(
                        document.level.value
                        if hasattr(document.level, "value")
                        else document.level
                    ),
                    source=f"{document.filename} (paragraph {i+1})",
                )
            )

        return passages

    def search(
        self,
        query: str,
        subject: str = None,
        level: str = None,
        k: int = 3,
        document_id: str = None,
    ) -> List[KnowledgePassage]:
        """
        Search for relevant passages based on query, subject, level, and optionally document_id.

        Args:
            query: The search query
            subject: Optional subject filter
            level: Optional level filter
            k: Number of results to return
            document_id: Optional document ID to search within a specific document

        Returns:
            List of relevant knowledge passages
        """
        all_passages = []

        # If a specific document is requested, search only within that document
        if document_id:
            document = self.document_service.get_document(document_id)
            if document:
                document_passages = self._document_to_passages(document)
                all_passages.extend(document_passages)
                logger.info(
                    f"Searching within document '{document.filename}' with {len(document_passages)} passages"
                )
            else:
                logger.warning(f"Document with ID {document_id} not found")
                # Still include static knowledge as fallback
                all_passages = self.passages
        else:
            # Otherwise search all static knowledge
            all_passages = self.passages

        # Filter by subject and level if provided
        candidates = all_passages
        if subject:
            candidates = [p for p in candidates if p.subject.lower() == subject.lower()]
        if level:
            candidates = [p for p in candidates if p.level.lower() == level.lower()]

        # Simple keyword matching (TODO: replace with vector search)
        query_terms = set(query.lower().split())
        scored_passages = []

        for passage in candidates:
            passage_terms = set(passage.text.lower().split())
            # Simple relevance score: count matching terms
            match_score = len(query_terms.intersection(passage_terms))
            scored_passages.append((passage, match_score))

        # Sort by score and return top k
        scored_passages.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in scored_passages[:k]]


class KnowledgeAugmentedTutor(dspy.Signature):
    """Tutor that retrieves relevant knowledge before answering."""

    question: str = dspy.InputField(desc="The student's question")
    subject: str = dspy.InputField(desc="The subject domain")
    level: str = dspy.InputField(desc="The difficulty level")
    knowledge: str = dspy.InputField(
        desc="Retrieved domain knowledge relevant to the question"
    )

    clarifying_question: str = dspy.OutputField(
        desc="A thoughtful question to guide the student's thinking and prompt deeper consideration of the topic"
    )
    concept_hint: str = dspy.OutputField(
        desc="A subtle hint that points toward relevant concepts without revealing answers. Focus on suggesting what to think about rather than explaining."
    )
    feedback: str = dspy.OutputField(
        desc="Encouraging and supportive feedback for the student"
    )


class RAGTutorModule(dspy.Module):
    """DSPy module that implements a RAG-augmented Socratic tutor."""

    def __init__(self, retriever=None):
        super().__init__()
        self.retriever = retriever or DocumentBasedRetriever()
        # Use ChainOfThought for better reasoning with retrieved knowledge
        self.tutor = dspy.ChainOfThought(KnowledgeAugmentedTutor)

    def forward(self, question: str, subject: str, level: str, document_id: str = None):
        """
        Process a student question using retrieved knowledge

        Args:
            question: The student's question
            subject: The subject domain
            level: The difficulty level
            document_id: Optional document ID to retrieve knowledge from

        Returns:
            DSPy prediction with clarifying_question, concept_hint, and feedback
        """
        # Retrieve relevant knowledge
        retrieved = self.retriever.search(
            query=question, subject=subject, level=level, k=3, document_id=document_id
        )

        # Combine retrieved knowledge
        if retrieved:
            knowledge = "\n\n".join([p.text for p in retrieved])
            sources = ", ".join(set(p.source for p in retrieved if p.source))
            logger.info(f"Retrieved {len(retrieved)} relevant passages from {sources}")
        else:
            knowledge = (
                "No specific knowledge found. Provide a general Socratic response."
            )
            logger.warning("No relevant knowledge retrieved")

        # Generate prediction with the retrieved knowledge
        prediction = self.tutor(
            question=question, subject=subject, level=level, knowledge=knowledge
        )

        return dspy.Prediction(
            clarifying_question=prediction.clarifying_question,
            concept_hint=prediction.concept_hint,
            feedback=prediction.feedback,
        )


class RAGTutorService:
    """Service class that handles the RAG-augmented tutor."""

    def __init__(
        self,
        openai_model: str = "gpt-4o",
        knowledge_path: str = None,
        document_service: DocumentService = None,
    ):
        """Initialize the service with the standard tutor service"""
        from app.dspy_modules import SocraticTutorService

        # Create the base service with the proper LM initialization
        self.base_service = SocraticTutorService(openai_model)

        # Create the document service
        self.document_service = document_service or DocumentService()

        # Create the retriever
        self.retriever = DocumentBasedRetriever(
            knowledge_path=knowledge_path, document_service=self.document_service
        )

        # Create the RAG module
        self.rag_module = None
        self.lm = self.base_service.lm  # Use the LM from the base service

    def get_socratic_response(
        self, question: str, subject: str, level: str, document_id: str = None
    ) -> Dict[str, str]:
        """
        Get a knowledge-augmented Socratic response for a student question

        Args:
            question: The student's question
            subject: The subject domain
            level: The difficulty level
            document_id: Optional document ID to retrieve knowledge from

        Returns:
            Dictionary with clarifying_question, concept_hint, and feedback
        """
        try:
            # Initialize the RAG module if needed
            if self.rag_module is None:
                # Configure DSPy with the LM from the base service
                dspy.configure(lm=self.lm)
                self.rag_module = RAGTutorModule(retriever=self.retriever)

            logger.info(
                f"Making RAG-augmented prediction for question: {question[:50]}..."
            )
            if document_id:
                logger.info(f"Using document ID: {document_id}")

            # Always reconfigure DSPy in Docker environments (addresses persistence issues)
            dspy.configure(lm=self.lm)

            # Get prediction from the RAG module
            try:
                prediction = self.rag_module.forward(
                    question=question,
                    subject=subject,
                    level=level,
                    document_id=document_id,
                )

                logger.info("RAG-augmented prediction successful")

                return {
                    "clarifying_question": prediction.clarifying_question,
                    "concept_hint": prediction.concept_hint,
                    "feedback": prediction.feedback,
                }
            except Exception as e:
                # Log the error and fall back to the base service
                logger.error(f"RAG-augmented prediction failed: {str(e)}")
                return self.base_service.get_socratic_response(question, subject, level)

        except Exception as e:
            # Log the error and fall back to the base service
            logger.error(f"Error in RAG service: {str(e)}")
            return self.base_service.get_socratic_response(question, subject, level)

    def upload_document(
        self, filename: str, content: str, subject: str, level: str, user_id: str = None
    ) -> Dict[str, Any]:
        """
        Upload a document for RAG-augmented tutoring

        Args:
            filename: Original filename
            content: Document text content
            subject: Academic subject
            level: Difficulty level
            user_id: Optional user identifier

        Returns:
            Document metadata
        """
        try:
            document = self.document_service.save_document(
                filename=filename,
                content=content,
                subject=subject,
                level=level,
                user_id=user_id,
            )

            return document.dict(exclude={"content"})
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise

    def get_documents(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get all documents, optionally filtered by user"""
        return self.document_service.get_all_documents(user_id)

    def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID"""
        return self.document_service.delete_document(document_id)
