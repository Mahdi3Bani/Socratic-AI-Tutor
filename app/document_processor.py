"""
Document Processor for Socratic AI Tutor

This module handles document parsing for different file formats.
"""

import os
import logging
from typing import Optional, Dict, Any, Tuple
import re

# Configure logging
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Class for processing uploaded documents into text format"""

    @staticmethod
    def process_document(
        file_content: bytes, filename: str
    ) -> Tuple[str, Optional[str]]:
        """
        Process a document file and extract its text content

        Args:
            file_content: Raw file content bytes
            filename: Original filename

        Returns:
            Tuple of (extracted_text, error_message)
        """
        # Get file extension
        _, ext = os.path.splitext(filename.lower())

        try:
            # Process based on file type
            if ext in [".txt", ".md"]:
                # Simple text files - try different encodings
                try:
                    return DocumentProcessor._process_text_file(file_content), None
                except UnicodeDecodeError:
                    return (
                        "",
                        "Could not decode text file. Please ensure it's in UTF-8 or common encoding.",
                    )

            elif ext in [".pdf"]:
                return DocumentProcessor._process_pdf(file_content), None

            elif ext in [".doc", ".docx"]:
                return DocumentProcessor._process_word_document(file_content), None

            else:
                return (
                    "",
                    f"Unsupported file type: {ext}. Please upload a .txt, .md, .pdf, .doc, or .docx file.",
                )

        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            return "", f"Error processing document: {str(e)}"

    @staticmethod
    def _process_text_file(content: bytes) -> str:
        """Process a simple text file"""
        # Try UTF-8 first
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            # Fall back to other common encodings
            try:
                return content.decode("latin-1")
            except:
                return content.decode(
                    "utf-8", errors="replace"
                )  # Last resort with replacement

    @staticmethod
    def _process_pdf(content: bytes) -> str:
        """Process a PDF file"""
        try:
            # Try to import PyPDF2
            import PyPDF2
            from io import BytesIO

            # Read PDF content
            pdf_file = BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Extract text from all pages
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"

            return text

        except ImportError:
            # If PyPDF2 is not available, return a message
            logger.warning("PyPDF2 not installed. PDF processing is unavailable.")
            return "PDF processing requires PyPDF2 library. Please install it or convert your PDF to text."

    @staticmethod
    def _process_word_document(content: bytes) -> str:
        """Process a Word document"""
        try:
            # Try to import docx
            import docx
            from io import BytesIO

            # Read DOCX content
            doc_file = BytesIO(content)
            doc = docx.Document(doc_file)

            # Extract text from all paragraphs
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"

            return text

        except ImportError:
            # If docx is not available, return a message
            logger.warning("python-docx not installed. DOCX processing is unavailable.")
            return "DOCX processing requires python-docx library. Please install it or convert your document to text."

    @staticmethod
    def chunk_document(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """
        Split document into overlapping chunks for better retrieval

        Args:
            text: Document text
            chunk_size: Target size of each chunk in characters
            overlap: Overlap between chunks in characters

        Returns:
            List of text chunks
        """
        # Clean up the text
        text = re.sub(r"\s+", " ", text).strip()

        # If text is shorter than chunk_size, return it as a single chunk
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # Get a chunk of approximately chunk_size characters
            end = start + chunk_size

            # If we're at the end of the text, just take what's left
            if end >= len(text):
                chunks.append(text[start:])
                break

            # Try to find a good breaking point (period, question mark, etc.)
            # Look for sentence endings within the last 20% of the chunk
            search_start = max(start, end - int(chunk_size * 0.2))
            next_period = text.find(". ", search_start, end + 100)
            next_question = text.find("? ", search_start, end + 100)
            next_exclamation = text.find("! ", search_start, end + 100)

            # Find the closest sentence ending
            candidates = [
                pos
                for pos in [next_period, next_question, next_exclamation]
                if pos != -1
            ]

            if candidates:
                # Use the earliest sentence ending we found (plus 2 to include the punctuation and space)
                end = min(candidates) + 2
            else:
                # If no sentence ending, try to break at a space
                space_pos = text.rfind(" ", search_start, end + 50)
                if space_pos != -1:
                    end = space_pos + 1

            # Add the chunk
            chunks.append(text[start:end])

            # Move to next chunk with overlap
            start = end - overlap

        return chunks
