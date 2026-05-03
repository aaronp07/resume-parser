import os
import json
import requests
import re

from typing import Any
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """
    You are an expert resume extraction. Given raw text extracted from a resume and extract all relevant information 
    and return to a single valid json object.
    
    Must be exactly following JSON schema:
    {
        "contact": {
            "name": string or null,
            "email": string or null,
            "mobile": string or null,
            "location": string or null,
            "linkedin": string or null,
            "github": string or null,
            "youtube": string or null,
            "website": string or null
        },
        "summary": string or null,
        "work_experience": [
            {
                "company": string or null,
                "role": string or null,
                "duration": string or null,
                "location": string or null,
                "responsibilities": [string]
            }
        ],
        "education": [
            {
            "degree": string or null,
            "institution": string or null,
            "year": string or null
            }
        ],
        "skills": {
            "technical": [string],
            "languages": [string]
        },
        "certifications": [
            {
            "name": string or null,
            "issuer": string or null,
            "year": string or null
            }
        ]
    }
Rules:
- Use null for any field you cannot find. Do not omit fields.
- responsibilities must always be an array of strings.
- skills.languages should include both programming languages and spoken/human languages.
- Return ONLY the JSON object. No surrounding text whatsoever.
"""

class LLMService:
    """Handles all interactions with a locally running Ollama instance"""
    
    # Constructor
    def __init__(self):
        self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:5000')
        self.model = os.getenv('OLLAMA_MODEL', 'mistral')
        self.timeout = os.getenv('OLLAMA_TIMEOUT', '120')
        logger.info(f'LLM Service constructor initialized - url: {self.base_url}, model: {self.model}')
        self.verify_connection()

    # Private helpers
    def verify_connection(self):
        """Warn early if Ollama is not reachable"""
        try:
            request = requests.get(f'{self.base_url}/api/tags', timeout=5)
            tags = [check_model('name', '') for check_model in request.json().get('models', [])]
            logger.info(f'Ollama reachable now and available models: {tags}')
            if not any(self.model in t for t in tags):
                logger.warning(f"Model: '{self.model}' not found locally. Run: ollama pull: '{self.model}'")
        except Exception:
            logger.warning(f"Could not reach Ollama at '{self.base_url}'. Ensure `ollama serve` is running before uploading resumes")
            
    # Public API
    def extract_content(self, resume_text: str) -> dict[str, Any]:
        """
        Send resume text to the local Ollama model and parse the JSON response.

        Args:
            resume_text: Raw text content of the resume.

        Returns:
            Dictionary matching the resume schema.

        Raises:
            ValueError: If the model returns content that cannot be parsed as JSON.
            ConnectionError: If Ollama is not reachable.
        """
        logger.debug(f"Sending {len(resume_text)} chars to Ollama ({self.model})")
        
        payload = {
            'model': self.model,
            'prompt': f'{SYSTEM_PROMPT} \n\nParse the following resume:\n\n{resume_text}',
            'stream': False
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/api/generate',
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot reach Ollama url: {self.base_url}, error: {e}")
            raise ConnectionError(f"Ollama is not running or not reachable url: {self.base_url}. Please start Ollama with `ollama serve` and ensure the model is pulled")
        except requests.exceptions.Timeout:
            raise ConnectionError(f"Ollama request timed out after {self.timeout}. Try a smaller/faster model or increase OLLAMA_TIMEOUT")
        except requests.exceptions.HTTPError as e:
            raise ValueError(f"Ollama API error: {e}") from e
        
        raw: str = response.json().get("response", "").strip()
        logger.debug(f"Raw Ollama response length: {len(raw)} characters")
        
        return self.parse_json(raw)
    
    # JSON Object
    def parse_json(self, raw: str) -> dict[str, Any]:
        """
        Robustly extract a JSON object from the model's raw text output

        Handles cases where the model wraps JSON in markdown fences or
        adds a preamble sentence before the actual object.
        """
        # 1. Strip markdown code fences
        clean = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        clean = re.sub(r"\s*```$", "", clean).strip()

        # 2. Try direct parse first
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            pass

        # 3. Find the first { ... } block (handles preamble text)
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        logger.error(f"Could not parse JSON from model response:\n{raw[:600]}")
        raise ValueError("The LLM did not return valid JSON. Try a different model (e.g. llama3, mistral) via the OLLAMA_MODEL env var")