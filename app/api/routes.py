from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from app.models import (
    StudentQuestion,
    SocraticResponse,
    HealthResponse,
    Subject,
    Level,
    Document,
)
from app.dspy_modules import (
    SocraticTutorService,
    EnsembleTutorService,
    AdvancedTutorService,
)
from app.rag_module import RAGTutorService
from app.optimizers import OptimizedTutorService
from app.document_processor import DocumentProcessor
from app.config import settings
import logging
from typing import List, Dict, Any, Optional
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize tutor service with the most advanced option
tutor_service = AdvancedTutorService(settings.OPENAI_MODEL)

# Initialize RAG tutor service
rag_service = None

# Initialize optimized tutor service
optimized_service = None


def get_tutor_service() -> SocraticTutorService:
    """Dependency to get or create the tutor service"""
    global tutor_service

    if tutor_service is None:
        if not settings.validate_openai_key():
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.",
            )

        try:
            tutor_service = SocraticTutorService(openai_model=settings.OPENAI_MODEL)
            logger.info(
                f"Initialized SocraticTutorService with model: {settings.OPENAI_MODEL}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize SocraticTutorService: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize AI tutor service: {str(e)}",
            )

    return tutor_service


def get_rag_service() -> RAGTutorService:
    """Dependency to get or create the RAG tutor service"""
    global rag_service

    if rag_service is None:
        if not settings.validate_openai_key():
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.",
            )

        try:
            rag_service = RAGTutorService(openai_model=settings.OPENAI_MODEL)
            logger.info(
                f"Initialized RAGTutorService with model: {settings.OPENAI_MODEL}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize RAGTutorService: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize RAG tutor service: {str(e)}",
            )

    return rag_service


def get_optimized_service() -> OptimizedTutorService:
    """Dependency to get or create the optimized tutor service"""
    global optimized_service

    if optimized_service is None:
        if not settings.validate_openai_key():
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.",
            )

        try:
            # Create the optimized service with MIPROv2
            optimized_service = OptimizedTutorService(
                openai_model=settings.OPENAI_MODEL, optimization_method="mipro"
            )
            logger.info(
                f"Initialized OptimizedTutorService with model: {settings.OPENAI_MODEL}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize OptimizedTutorService: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize optimized tutor service: {str(e)}",
            )

    return optimized_service


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", message="Socratic AI Tutor is running")


@router.post("/tutor", response_model=SocraticResponse)
async def get_socratic_guidance(
    question_data: StudentQuestion,
    service: SocraticTutorService = Depends(get_tutor_service),
):
    """
    Get Socratic-style guidance for a student question

    This endpoint takes a student question with subject and level context,
    and returns a structured response with:
    - A clarifying question to guide thinking
    - A concept hint without giving away the answer
    - Encouraging feedback
    """
    try:
        logger.info(
            f"Processing question: {question_data.question[:50]}... "
            f"(Subject: {question_data.subject}, Level: {question_data.level})"
        )

        # Get response from DSPy service
        response_data = service.get_socratic_response(
            question=question_data.question,
            subject=question_data.subject,
            level=question_data.level,
        )

        logger.info("Successfully generated Socratic response")

        return SocraticResponse(**response_data)

    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process question: {str(e)}"
        )


@router.post("/tutor/rag", response_model=SocraticResponse)
async def get_rag_socratic_guidance(
    question_data: StudentQuestion,
    service: RAGTutorService = Depends(get_rag_service),
):
    """
    Get knowledge-enhanced Socratic-style guidance for a student question

    This endpoint uses RAG (Retrieval Augmented Generation) to provide responses
    grounded in domain-specific knowledge or uploaded documents.
    """
    try:
        logger.info(
            f"Processing RAG question: {question_data.question[:50]}... "
            f"(Subject: {question_data.subject}, Level: {question_data.level})"
        )

        if question_data.document_id:
            logger.info(f"Using document ID: {question_data.document_id}")

        # Get response from RAG service
        response_data = service.get_socratic_response(
            question=question_data.question,
            subject=question_data.subject,
            level=question_data.level,
            document_id=question_data.document_id,
        )

        logger.info("Successfully generated knowledge-enhanced Socratic response")

        return SocraticResponse(**response_data)

    except Exception as e:
        logger.error(f"Error processing RAG question: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process RAG question: {str(e)}"
        )


@router.post("/documents/upload", response_model=Dict[str, Any])
async def upload_document(
    file: UploadFile = File(...),
    subject: str = Form(...),
    level: str = Form(...),
    user_id: Optional[str] = Form(None),
    service: RAGTutorService = Depends(get_rag_service),
):
    """
    Upload a document for RAG-based tutoring

    This endpoint accepts various document formats (txt, pdf, docx) and processes them for use in knowledge retrieval.
    """
    try:
        # Validate subject and level
        try:
            subject_enum = Subject(subject)
            level_enum = Level(level)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid subject or level. Valid subjects: {[s.value for s in Subject]}, valid levels: {[l.value for l in Level]}",
            )

        # Read file content
        content = await file.read()

        # Process the document
        text_content, error = DocumentProcessor.process_document(content, file.filename)

        # Check for processing errors
        if error:
            raise HTTPException(status_code=400, detail=error)

        # Check if we have valid content
        if not text_content or len(text_content.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Document appears to be empty or could not be processed properly.",
            )

        # Chunk the document if it's large
        if len(text_content) > 10000:  # If more than ~10KB of text
            chunks = DocumentProcessor.chunk_document(text_content)
            logger.info(f"Large document split into {len(chunks)} chunks")

            # For now, just use the first chunk that's reasonably sized
            if len(chunks) > 0:
                text_content = chunks[0]  # Use first chunk

                # Log a warning that we're not using the full document
                logger.warning(
                    f"Document too large, using only first chunk ({len(text_content)} chars)"
                )

        # Limit final content size
        if len(text_content) > 100000:  # ~100KB limit
            text_content = text_content[:100000]
            logger.warning("Document truncated to 100KB")

        # Upload the processed document
        document = service.upload_document(
            filename=file.filename,
            content=text_content,
            subject=subject_enum,
            level=level_enum,
            user_id=user_id,
        )

        logger.info(
            f"Document uploaded: {file.filename}, id: {document['id']}, size: {len(text_content)} chars"
        )

        return {
            "message": "Document uploaded and processed successfully",
            "document": document,
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/documents", response_model=List[Dict[str, Any]])
async def get_documents(
    user_id: Optional[str] = None,
    service: RAGTutorService = Depends(get_rag_service),
):
    """
    Get a list of uploaded documents

    Optionally filter by user_id
    """
    try:
        documents = service.get_documents(user_id)
        return documents
    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve documents: {str(e)}"
        )


@router.delete("/documents/{document_id}", response_model=Dict[str, Any])
async def delete_document(
    document_id: str,
    service: RAGTutorService = Depends(get_rag_service),
):
    """
    Delete a document by ID
    """
    try:
        success = service.delete_document(document_id)
        if success:
            return {"message": f"Document {document_id} deleted successfully"}
        else:
            raise HTTPException(
                status_code=404, detail=f"Document {document_id} not found"
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete document: {str(e)}"
        )


@router.post("/tutor/optimized", response_model=SocraticResponse)
async def get_optimized_socratic_guidance(
    question_data: StudentQuestion,
    service: OptimizedTutorService = Depends(get_optimized_service),
):
    """
    Get optimized Socratic-style guidance for a student question

    This endpoint uses DSPy's optimization capabilities (MIPROv2) to provide
    higher-quality responses through prompt optimization.
    """
    try:
        logger.info(
            f"Processing optimized question: {question_data.question[:50]}... "
            f"(Subject: {question_data.subject}, Level: {question_data.level})"
        )

        # Get response from optimized service
        response_data = service.get_socratic_response(
            question=question_data.question,
            subject=question_data.subject,
            level=question_data.level,
        )

        logger.info("Successfully generated optimized Socratic response")

        return SocraticResponse(**response_data)

    except Exception as e:
        logger.error(f"Error processing optimized question: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process optimized question: {str(e)}"
        )


@router.get("/subjects")
async def get_available_subjects():
    """Get list of available subjects"""
    from app.models import Subject

    return {"subjects": [subject.value for subject in Subject]}


@router.get("/levels")
async def get_available_levels():
    """Get list of available difficulty levels"""
    from app.models import Level

    return {"levels": [level.value for level in Level]}
