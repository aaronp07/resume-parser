import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.services.parser import ResumeParserService
from app.models import ResumeModel, UploadResume
from app.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title='Resume Parser API',
    description='Extract structured information from resumes using LLM',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# Set the uploads directory and create folder
UPLOAD_DIR = Path('data/uploads')
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# In-memory store for parse resumes
resume_store: dict[str, Any] = {}

# Create instance - Parser from services
parser_service = ResumeParserService()

@app.get('/', tags=['Health'])
async def root() -> dict:
    """Health check endpoint"""
    return {'status': 'ok', 'message': 'Resume Parser API is running'}

@app.post('/api/upload', response_model=UploadResume, tags=['Resume'])
async def upload_resume(file: UploadFile=File(...)) -> UploadResume:
    """
    Upload and parse a resume file (PDF or DOCX)

    Args:
        file (UploadResume, optional): The resume file to upload and parse

    Returns:
        Extracted resume data along with a unique document id
    """
    allowed_types = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingxml.document'
    }
    
    if file.content_type not in allowed_types:
        logger.warning(f'Rejected file with content type: {file.content_type}')
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Only PDF or DOCX are allowed"
        )
    
    suffix = '.pdf' if file.content_type == 'application/pdf' else '.docx'
    document_id = str(uuid.uuid4()) # Random number
    save_path = UPLOAD_DIR / f'{document_id}{suffix}'
    
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail='Uploaded file is empty')
        save_path.write_bytes(content)
        logger.info(f'Save uploaded file to {save_path}')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Failed to save the file: {e}')
        raise HTTPException(status_code=500, detail='Failed to save uploaded file')
    
    try:
        resume_data = await parser_service.parse(save_path, file.content_type)
        logger.info(f'Successfully parsed resume: {document_id}')
    except ConnectionError as e:
        logger.error(f'Ollama connection error for {document_id}: {e}')
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        logger.error(f'Parsing error for {document_id}: {e}')
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f'Unexpected error parsing {document_id}: {e}')
        raise HTTPException(status_code=500, detail='Failed to parse resume, please try again')
    
    resume_store[document_id] = resume_data.model_dump()
    
    return UploadResume(document_id=document_id, resume=resume_data)

@app.get('/api/resume/{document_id}', response_model=ResumeModel, tags=['Resume'])
async def get_resume(document_id: str) -> ResumeModel:
    """
    Retrieve previously extracted resume data by document id

    Args:
        document_id (str): The unique identifier returned when the resume was uploaded

    Returns:
        404 if the document is not found
    """
    data = resume_store.get(document_id)
    if data is None:
        logger.warning(f'Resume not found: {document_id}')
        raise HTTPException(status_code=404, detail=f"Resume with id: '{document_id}' not found")
    logger.info(f'Retrieved resume: {document_id}')
    return ResumeModel(**data)