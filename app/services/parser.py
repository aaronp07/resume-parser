from pathlib import Path
import fitz # PyMuPDF library
from docx import Document
from typing import Any

from app.services.llm_service import LLMService
from app.model import (ContactInfo, WorkExperience, Education, Skills, Certification, ResumeModel)
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ResumeParserService:
    """Reading the file and LLM-based data extraction"""
    def __init__(self):
        self.llm = LLMService()
        
    async def parse(self, file_path: Path, content_type: str) -> ResumeModel:
        """
        Extract structured resume data from PDF or DOCX file

        Args:
            file_path (Path): Path to uploaded file
            content_type (str): MIME type of the file

        Returns:
            Validation: Resume model instance
        
        Raises:
            ValueError: If the file cannot be read or parsed
        """
        text = self.extract_content(file_path, content_type)
        if not text.strip():
            raise ValueError('Could not extract any text from the uploaded file')
        
        logger.info(f'Extracted content length: {len(text)} characters of text from {file_path.name}')
        raw_data = self.llm.extract_content(resume_text=text)
        return self.build_object(raw_data, len(text))
    
    # Model builder
    def build_object(self, data: dict[str, Any], text_length: int) -> ResumeModel:
        """Map with raw data to LLM dictionary to validate pydantic models"""
        
        # Get - Contact Information
        raw_content = data.get('contact') or {}
        contact = ContactInfo(
            name=raw_content.get('name'),
            email=raw_content.get("email"),
            mobile=raw_content.get("mobile"),
            location=raw_content.get("location"),
            linkedin=raw_content.get("linkedin"),
            github=raw_content.get("github"),
            youtube=raw_content.get("youtube"),
            website=raw_content.get("website")
        )
        
        # Work Experience
        work_experience = [
            WorkExperience(
                company=we.get("company"),
                role=we.get("role"),
                duration=we.get("duration"),
                location=we.get("location"),
                responsibilities=we.get("responsibilities") or []
            )
            for we in (data.get("work_experience") or [])
        ]

        # Education
        education = [
            Education(
                degree=edu.get("degree"),
                institution=edu.get("institution"),
                year=edu.get("year")
            )
            for edu in (data.get("education") or [])
        ]

        # Skills
        skills_raw = data.get("skills") or {}
        skills = Skills(
            technical=skills_raw.get("technical") or [],
            languages=skills_raw.get("languages") or []
        )

        certifications = [
            Certification(
                name=cert.get("name"),
                issuer=cert.get("issuer"),
                year=cert.get("year")
            )
            for cert in (data.get("certifications") or [])
        ]

        return ResumeModel(
            contact=contact,
            summary=data.get("summary"),
            work_experience=work_experience,
            education=education,
            skills=skills,
            certifications=certifications,
            raw_text_count=text_length
        )
    
    # Extract the raw content from PDF/DOCX
    def extract_content(self, file_path: Path, content_type: str) -> str:
        """Extract the content from PDF or DOCX file"""
        if content_type == 'application/pdf':
            try:
                with fitz.open(str(file_path)) as doc:
                    content = [page.get_text() for page in doc]
                    return '\n'.join(content)
            except Exception as e:
                logger.error(f'PDF extraction failed - {file_path}: {e}')
                raise ValueError(f'Failed to read PDF file: {e}')
            
        elif content_type == 'application/docx':
            try:
                doc = Document(str(file_path))
                content = [para.text for para in doc.paragraphs if para.text.strip()]
                return '\n'.join(content)
            except Exception as e:
                logger.error(f'Document extraction failed - {file_path}: {e}')
                raise ValueError(f'Failed to read DOCX file: {e}')
        else:
            raise ValueError(f'Unsupported content type: {content_type}')