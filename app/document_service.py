"""
Document Service for Socratic AI Tutor

This module handles document storage, retrieval, and processing for the RAG system.
"""

import os
import json
import uuid
import logging
import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
from app.models import Document, Subject, Level

# Configure logging
logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing uploaded documents"""

    def __init__(self, documents_dir: str = None):
        """Initialize the document service with a storage directory"""
        self.documents_dir = documents_dir or os.path.join(
            os.path.dirname(__file__), "../data/documents"
        )

        # Create documents directory if it doesn't exist
        os.makedirs(self.documents_dir, exist_ok=True)

        # In-memory cache of documents
        self.documents = {}

        # Load existing documents
        self._load_documents()

    def _load_documents(self):
        """Load documents from storage directory"""
        try:
            document_files = Path(self.documents_dir).glob("*.json")
            for file_path in document_files:
                with open(file_path, "r", encoding="utf-8") as f:
                    doc_data = json.load(f)
                    doc_id = file_path.stem  # Use filename without extension as ID
                    self.documents[doc_id] = Document(**doc_data)

            logger.info(f"Loaded {len(self.documents)} documents from storage")
        except Exception as e:
            logger.error(f"Error loading documents: {str(e)}")

    def save_document(
        self,
        filename: str,
        content: str,
        subject: Subject,
        level: Level,
        user_id: str = None,
    ) -> Document:
        """
        Save a new document and return its metadata

        Args:
            filename: Original filename
            content: Document text content
            subject: Academic subject
            level: Difficulty level
            user_id: Optional user identifier

        Returns:
            Document object with metadata
        """
        try:
            # Generate unique ID
            doc_id = str(uuid.uuid4())

            # Create document object
            document = Document(
                id=doc_id,
                filename=filename,
                content=content,
                subject=subject,
                level=level,
                created_at=datetime.datetime.now().isoformat(),
                user_id=user_id,
            )

            # Save to in-memory cache
            self.documents[doc_id] = document

            # Save to disk
            file_path = os.path.join(self.documents_dir, f"{doc_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                # Convert to dict, but exclude the content for logging
                doc_dict = document.dict()
                logger.info(f"Saving document: {filename} ({len(content)} characters)")
                json.dump(doc_dict, f, indent=2)

            return document

        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            raise

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID"""
        return self.documents.get(doc_id)

    def get_all_documents(self, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all documents, optionally filtered by user

        Returns a list of document metadata without the content field
        to avoid sending large amounts of data
        """
        result = []

        for doc in self.documents.values():
            if user_id is None or doc.user_id == user_id:
                # Return metadata without content
                doc_dict = doc.dict(exclude={"content"})
                result.append(doc_dict)

        return result

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID"""
        try:
            if doc_id in self.documents:
                # Remove from memory
                del self.documents[doc_id]

                # Remove from disk
                file_path = os.path.join(self.documents_dir, f"{doc_id}.json")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted document {doc_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
