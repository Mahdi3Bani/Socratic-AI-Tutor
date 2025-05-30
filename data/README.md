# Document Storage for Socratic AI Tutor

This directory stores uploaded documents that students can use to enhance the AI Tutor's responses.

## Directory Structure

- `documents/` - Stores the uploaded document JSON files with content and metadata

## How Document Upload Works

1. Students upload documents through the frontend interface
2. Documents are processed based on file type:
   - Text files (.txt, .md) - Directly extracted as text
   - PDF files (.pdf) - Text extracted using PyPDF2
   - Word documents (.doc, .docx) - Text extracted using python-docx
3. Large documents are chunked into smaller sections for better retrieval
4. Documents are stored as JSON files with a unique ID
5. When asking questions, students can select a specific document to use as context

## Document Format

Each document is stored as a JSON file with the following structure:

```json
{
  "id": "unique-document-id",
  "filename": "original-filename.pdf",
  "content": "Extracted text content of the document",
  "subject": "math",
  "level": "intermediate",
  "created_at": "2025-05-29T10:30:00.000Z",
  "user_id": "optional-user-identifier"
}
```

## RAG Implementation

The Retrieval-Augmented Generation (RAG) system works as follows:

1. When a student asks a question with a document selected, the system retrieves the document
2. The document text is split into passages
3. The system searches for passages most relevant to the student's question
4. These passages are provided as context to the LLM along with the question
5. The LLM generates a Socratic response incorporating knowledge from the document

This approach allows the tutor to provide personalized guidance based on the student's own learning materials. 