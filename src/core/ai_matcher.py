from src.database.chroma_db import ChromaDB
from src.utils.file_parser import CVParser
from src.utils.text_cleaner import TextCleaner
from src.llm.openai_client import OpenAIClient
from config import LLM_PROVIDER

# Conditionally import Claude client only if requested
if LLM_PROVIDER == 'claude':
    try:
        from src.llm.claude_client import ClaudeClient
    except Exception:
        ClaudeClient = None
import re
import json

class AIMatcher:
    def __init__(self):
        self.db = ChromaDB()
        self.parser = CVParser()
        self.cleaner = TextCleaner()
        # Choose LLM client based on config; default to OpenAIClient
        if LLM_PROVIDER == 'claude' and 'ClaudeClient' in globals() and ClaudeClient:
            try:
                self.llm_client = ClaudeClient()
                print("✅ AI Matcher initialized - Using Claude client for LLM calls")
            except Exception as e:
                print(f"⚠️ Failed to initialize Claude client, falling back to OpenAIClient: {e}")
                self.llm_client = OpenAIClient()
        else:
            self.llm_client = OpenAIClient()
        print("✅ AI Matcher initialized - Enhanced extraction enabled")
    
    def process_and_store_cv(self, file_path, candidate_name):
        print(f"📄 Processing CV: {candidate_name}")
        
        try:
            raw_text = self.parser.parse_cv(file_path)
            print(f"📝 Extracted {len(raw_text)} characters")
            
            if "error" in raw_text.lower():
                return {"error": raw_text}
            
            cleaned_text = self.cleaner.clean_text(raw_text)
            
            print("🤖 Asking OpenAI to detect skills...")
            skills = self.llm_client.extract_skills(cleaned_text)
            
            print("🤖 Comprehensive AI analysis starting...")
            comprehensive_details = self.llm_client.extract_comprehensive_details(cleaned_text)
            
            personal_info = comprehensive_details.get('personal_info', {})
            professional_info = comprehensive_details.get('professional_info', {})
            education_info = comprehensive_details.get('education', {})
            technical_skills = comprehensive_details.get('technical_skills', {})
            
            actual_name = personal_info.get('full_name', candidate_name)
            
            clean_skills = [skill for skill in skills if skill and skill.lower() not in ['extracted', 'ai analyzing', 'no skills']]
            
            # FORMAT EDUCATION - Convert to bullet points
            education_text = self.format_education_text(education_info, cleaned_text)
            
            # FORMAT SUMMARY - Convert to bullet points
            summary_text = self.format_summary_text(professional_info.get('summary', ''), cleaned_text)
            
            # FORMAT CV PREVIEW - Clean and structure
            formatted_preview = self.format_cv_preview(cleaned_text)
            
            metadata = {
                'candidate_name': str(actual_name),
                'skills': ', '.join(clean_skills) if clean_skills else "Technical Skills",
                'email': personal_info.get('email', 'Email in CV'),
                'phone': personal_info.get('phone', 'Phone in CV'),
                'address': personal_info.get('address', 'Address in CV'),
                'location': personal_info.get('location', 'Location in CV'),
                'current_role': professional_info.get('current_role', 'Professional Role'),
                'experience': professional_info.get('total_experience', 'Experience in CV'),
                'current_company': professional_info.get('current_company', 'Company in CV'),
                'education': education_text,
                'summary': summary_text,
                'programming_languages': ', '.join(technical_skills.get('programming_languages', [])),
                'frameworks': ', '.join(technical_skills.get('frameworks', [])),
                'databases': ', '.join(technical_skills.get('databases', [])),
                'cloud_platforms': ', '.join(technical_skills.get('cloud_platforms', [])),
                'raw_text': formatted_preview
            }
            
            print(f"📊 AI Analysis Complete:")
            print(f"   👤 Name: {actual_name}")
            print(f"   📧 Email: {metadata['email']}")
            print(f"   📞 Phone: {metadata['phone']}")
            print(f"   🔧 Skills: {len(clean_skills)} skills")
            
            cv_id = self.db.add_cv(cleaned_text, metadata)
            
            return {
                'cv_id': cv_id, 
                'skills': clean_skills,
                'comprehensive_details': comprehensive_details,
                'text_length': len(cleaned_text)
            }
            
        except Exception as e:
            print(f"❌ CV processing failed: {e}")
            return {"error": str(e)}
    
    def format_education_text(self, education_info, raw_text):
        """Format education information as bullet points"""
        highest_degree = education_info.get('highest_degree', '')
        university = education_info.get('university', '')
        qualifications = education_info.get('qualifications', '')
        
        education_points = []
        
        if highest_degree and highest_degree != "Education in CV":
            education_points.append(f"• {highest_degree}")
        
        if university and university != "University in CV":
            education_points.append(f"• {university}")
        
        if qualifications and qualifications != "Qualifications in CV":
            qual_list = [q.strip() for q in qualifications.split(',') if q.strip()]
            for qual in qual_list[:3]:
                education_points.append(f"• {qual}")
        
        if not education_points:
            education_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'college', 'bs', 'ms', 'btech', 'mtech']
            lines = raw_text.split('\n')
            for line in lines:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in education_keywords) and len(line.strip()) > 10:
                    education_points.append(f"• {line.strip()}")
                    if len(education_points) >= 2:
                        break
        
        if education_points:
            return "\n".join(education_points[:4])
        else:
            return "• Educational qualifications detailed in CV\n• Professional certifications\n• University degree"
    
    def format_summary_text(self, summary, raw_text):
        """Format summary as bullet points"""
        if not summary or "technical expertise" in summary.lower():
            lines = raw_text.split('\n')
            key_points = []
            
            achievement_keywords = ['developed', 'created', 'managed', 'led', 'implemented', 'achieved', 'built']
            for line in lines[:20]:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in achievement_keywords) and len(line.strip()) > 20:
                    key_points.append(f"• {line.strip()}")
                    if len(key_points) >= 3:
                        break
            
            if key_points:
                return "\n".join(key_points)
            else:
                return "• Experienced professional with technical expertise\n• Strong problem-solving skills\n• Excellent communication abilities"
        
        sentences = re.split(r'[.!?]+', summary)
        bullet_points = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 15 and len(bullet_points) < 4:
                bullet_points.append(f"• {sentence}")
        
        return "\n".join(bullet_points) if bullet_points else summary
    
    def format_cv_preview(self, text):
        """Format CV preview with better structure"""
        lines = text.split('\n')
        formatted_lines = []
        
        sections = []
        current_section = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if (len(line) < 50 and 
                (line.isupper() or 
                 any(keyword in line.lower() for keyword in ['experience', 'education', 'skills', 'projects', 'summary']))):
                if current_section:
                    sections.append(current_section)
                current_section = [f"\n{line.upper()}"]
            else:
                current_section.append(f"• {line}")
        
        if current_section:
            sections.append(current_section)
        
        preview_lines = []
        char_count = 0
        for section in sections[:6]:
            for line in section:
                if char_count + len(line) < 800:
                    preview_lines.append(line)
                    char_count += len(line)
        
        return "\n".join(preview_lines) if preview_lines else text[:800]
    
    def find_matching_cvs(self, job_description, top_k=5):
        print(f"🔍 Searching for: {job_description}")
        results = self.db.search_similar(job_description, top_k)
        
        # Log search results for debugging
        if results and results['metadatas'] and results['metadatas'][0]:
            print(f"✅ Found {len(results['metadatas'][0])} matching CVs")
            for i, metadata in enumerate(results['metadatas'][0]):
                print(f"   {i+1}. {metadata.get('candidate_name', 'Unknown')} - {results['distances'][0][i]}%")
        else:
            print("❌ No matching CVs found")
            
        return results