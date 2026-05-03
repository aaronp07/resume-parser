from typing import Optional
from pydantic import BaseModel, Field

# Contact Information
class ContactInfo(BaseModel):
    """Extract the contact information from resume"""
    name: Optional[str] = Field(None, description="Full name of the candidate")
    email: Optional[str] = Field(None, description="Email id")
    mobile: Optional[str] = Field(None, description="Contact number")
    location: Optional[str] = Field(None, description="City, State and Country")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile url")
    github: Optional[str] = Field(None, description="Github profile url")
    youtube: Optional[str] = Field(None, description="YouTube url")
    website: Optional[str] = Field(None, description="Personally deployed website")
    
# Work Experience
class WorkExperience(BaseModel):
    """Extract a single work experience"""
    company: Optional[str] = Field(None, description="Name of the company")
    role: Optional[str] = Field(None, description="Job title or role")
    duration: Optional[str] = Field(None, description="Duration, e.g. 'July-2017' to April-2026")
    location: Optional[str] = Field(None, description="Work location")
    responsibilities: list[str] = Field(None, description="Key responsibilities and achievements")
    
# Education
class Education(BaseModel):
    """Extract a single education information"""
    degree: Optional[str] = Field(None, description="Degree or Qualification")
    institution: Optional[str] = Field(None, description="School or Name of the university")
    year: Optional[str] = Field(None, description="Graduated year or date range")
    
# Skills
class Skills(BaseModel):
    """Extract list of skills from the resume"""
    technical: list[str] = Field(None, description="Technical skills")
    language: list[str] = Field(None, description="Programming language or Spoken languages")    
    
# Certifications
class Certification(BaseModel):
    """Extract a single certificate information"""
    name: Optional[str] = Field(None, description="Name of the certificate")
    issuer: Optional[str] = Field(None, description="Issuing organization")
    year: Optional[str] = Field(None, description="Year of completed or expiry")
    
# Combine the model
class ResumeModel(BaseModel):
    """Complete structure of resume data and return parser"""
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: Optional[str] = Field(None, description="Professional summary")
    work_experience: list[WorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    certifications: list[Certification] = Field(default_factory=list)
    raw_text_count: Optional[int] = Field(None, description="Count the character of extracted raw text")
    
# Uploaded Resume
class UploadResume(BaseModel):
    """Response return after successfully file uploaded and parse"""
    document_id: str = Field(..., description="Retrieve the resume document with unique id")
    resume: ResumeModel