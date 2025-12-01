from .openai_client import OpenAIClient
import json
import re

class CVAnalyzer:
    def __init__(self):
        self.llm_client = OpenAIClient()
    
    def analyze_cv_details(self, text):
        try:
            analysis = self.llm_client.analyze_cv(text)
            if analysis and analysis.strip():
                return json.loads(analysis)
        except:
            pass
        return self.fallback_analysis(text)
    
    def fallback_analysis(self, text):
        text_lower = text.lower()
        
        # Extract name (first line usually)
        name = "Unknown Candidate"
        lines = text.split('\n')
        if lines and len(lines[0].strip()) > 0:
            name = lines[0].strip()[:50]
        
        # Extract email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        email = email_match.group(0) if email_match else "Not found"
        
        # Extract phone
        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        phone = phone_match.group(0) if phone_match else "Not found"
        
        # Extract experience
        exp_match = re.search(r'(\d+)\s*(?:years?|yrs?)', text_lower)
        experience = exp_match.group(1) + " years" if exp_match else "Not specified"
        
        return {
            "name": name,
            "email": email,
            "phone": phone,
            "experience": experience,
            "skills": [],
            "education": "Extracted from CV",
            "summary": "AI analysis pending"
        }