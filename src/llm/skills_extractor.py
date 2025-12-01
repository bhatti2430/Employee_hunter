from .openai_client import OpenAIClient
import re

class SkillsExtractor:
    def __init__(self):
        self.llm_client = OpenAIClient()
    
    def extract_with_ai(self, text):
        ai_skills = self.llm_client.extract_skills(text)
        if ai_skills:
            return ai_skills
        return self.fallback_extraction(text)
    
    def fallback_extraction(self, text):
        text_lower = text.lower()
        skills_found = set()
        
        skill_categories = {
            'python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy'],
            'java': ['java', 'spring', 'hibernate', 'maven', 'gradle'],
            'javascript': ['javascript', 'typescript', 'node.js', 'react', 'angular', 'vue', 'express'],
            'database': ['mysql', 'postgresql', 'mongodb', 'sql', 'oracle', 'redis'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins'],
            'mobile': ['android', 'ios', 'flutter', 'react native'],
            'ml_ai': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'nlp', 'computer vision']
        }
        
        for category, keywords in skill_categories.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    skills_found.add(category)
                    break
        
        return list(skills_found)