import openai
from config import OPENAI_API_KEY
import re
import json

class OpenAIClient:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
    
    def extract_skills(self, text):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are an expert HR technical analyst. Extract ALL technical skills, programming languages, frameworks, tools, and technologies from the CV text. 
                        Be VERY comprehensive and thorough. Look for ANY mention of technical skills.
                        Return ONLY a comma-separated list of specific skills.
                        IMPORTANT: If you find ANY technical terms, include them.
                        Example: Python, JavaScript, React.js, Node.js, MySQL, MongoDB, AWS, Docker, Git, Machine Learning, TensorFlow"""
                    },
                    {
                        "role": "user",
                        "content": f"Extract ALL technical skills from this CV. Be very thorough:\n\n{text[:3500]}"
                    }
                ],
                max_tokens=800,
                temperature=0.3
            )
            skills_text = response.choices[0].message.content.strip()
            skills = [skill.strip() for skill in skills_text.split(',') if skill.strip()]
            print(f"🤖 OpenAI detected {len(skills)} skills: {skills}")
            return skills
            
        except Exception as e:
            print(f"⚠️ OpenAI failed, using advanced fallback: {e}")
            return self.advanced_fallback_skills(text)
    
    def advanced_fallback_skills(self, text):
        """Advanced skill extraction with better patterns"""
        text_lower = text.lower()
        skills_found = set()
        
        # Comprehensive skill patterns
        skill_patterns = {
            'Python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'tensorflow', 'pytorch'],
            'Java': ['java', 'spring', 'hibernate', 'spring boot', 'j2ee', 'javafx'],
            'JavaScript': ['javascript', 'typescript', 'nodejs', 'react', 'angular', 'vue', 'express', 'jquery'],
            'Database': ['mysql', 'mongodb', 'postgresql', 'sql', 'oracle', 'redis', 'sqlite', 'firebase'],
            'Cloud': ['aws', 'azure', 'google cloud', 'docker', 'kubernetes', 'jenkins', 'ci/cd'],
            'Mobile': ['android', 'ios', 'react native', 'flutter', 'kotlin', 'swift'],
            'AI/ML': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'nlp', 'computer vision', 'neural networks'],
            'Web': ['html', 'css', 'bootstrap', 'rest api', 'graphql', 'websocket', 'json', 'xml'],
            'Tools': ['git', 'github', 'gitlab', 'jira', 'linux', 'windows', 'macos', 'visual studio', 'eclipse'],
            'Data Analysis': ['data analysis', 'data visualization', 'tableau', 'power bi', 'excel', 'statistics'],
            'Web Scraping': ['web scraping', 'beautifulsoup', 'scrapy', 'selenium', 'requests']
        }
        
        for skill, keywords in skill_patterns.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    skills_found.add(skill)
                    break
        
        skills_list = list(skills_found)
        print(f"🔧 Advanced fallback detected {len(skills_list)} skills: {skills_list}")
        return skills_list
    
    def extract_comprehensive_details(self, text):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert CV analyst. Extract COMPLETE details from the CV in JSON format. Be very thorough and accurate.

                        Return EXACTLY this JSON structure:
                        {
                            "personal_info": {
                                "full_name": "complete name",
                                "email": "email address - EXTRACT THIS CAREFULLY",
                                "phone": "phone number with country code",
                                "address": "complete address if available",
                                "location": "city, country",
                                "linkedin": "linkedin profile if mentioned"
                            },
                            "professional_info": {
                                "current_role": "current job title",
                                "total_experience": "X years",
                                "current_company": "current company name",
                                "summary": "2-3 line professional summary"
                            },
                            "education": {
                                "highest_degree": "highest qualification",
                                "university": "university name", 
                                "graduation_year": "year of graduation",
                                "qualifications": "list all degrees and certifications"
                            },
                            "technical_skills": {
                                "programming_languages": ["list of languages"],
                                "frameworks": ["list of frameworks"],
                                "tools": ["list of tools"],
                                "databases": ["list of databases"],
                                "cloud_platforms": ["list of cloud platforms"]
                            }
                        }

                        IMPORTANT: Find the email address carefully, it's usually in contact section"""
                    },
                    {
                        "role": "user",
                        "content": f"Extract COMPLETE details from this CV. Pay special attention to email and education:\n\n{text[:4000]}"
                    }
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            print(f"🤖 OpenAI raw response: {result_text[:200]}...")
            
            try:
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    cv_details = json.loads(json_str)
                    print("✅ Successfully parsed OpenAI JSON response")
                    
                    # Validate and enhance email extraction
                    email = cv_details.get('personal_info', {}).get('email', '')
                    if not self.is_valid_email(email):
                        enhanced_email = self.enhanced_email_extraction(text)
                        cv_details['personal_info']['email'] = enhanced_email
                    
                    return cv_details
                else:
                    print("❌ No JSON found in OpenAI response")
                    return self.enhanced_fallback_analysis(text)
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                return self.enhanced_fallback_analysis(text)
                
        except Exception as e:
            print(f"⚠️ OpenAI analysis failed, using enhanced fallback: {e}")
            return self.enhanced_fallback_analysis(text)
    
    def enhanced_fallback_analysis(self, text):
        """Enhanced fallback analysis with better extraction"""
        print("🔧 Using enhanced fallback analysis")
        
        # Enhanced email extraction
        print("🔍 Searching for email in text...")
        email = self.enhanced_email_extraction(text)
        
        # Enhanced phone extraction
        print("🔍 Searching for phone in text...")
        phone = self.enhanced_phone_extraction(text)
        
        # Enhanced name extraction
        full_name = self.enhanced_name_extraction(text)
        
        # Enhanced location extraction
        location = self.enhanced_location_extraction(text)
        
        # Enhanced role extraction
        current_role = self.enhanced_role_extraction(text)
        
        # Enhanced experience extraction
        total_experience = self.enhanced_experience_extraction(text)
        
        # Enhanced company extraction
        current_company = self.enhanced_company_extraction(text)
        
        # Enhanced education extraction
        education_info = self.enhanced_education_extraction(text)
        
        # Enhanced technical skills
        technical_skills = self.enhanced_skills_categorization(text)
        
        return {
            "personal_info": {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "address": "Address in CV",
                "location": location,
                "linkedin": ""
            },
            "professional_info": {
                "current_role": current_role,
                "total_experience": total_experience,
                "current_company": current_company,
                "summary": f"Experienced {current_role} with expertise in technical development and problem-solving"
            },
            "education": education_info,
            "technical_skills": technical_skills
        }
    
    def enhanced_email_extraction(self, text):
        """Enhanced email extraction with multiple methods"""
        # Method 1: Direct regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, text)
        
        for email in email_matches:
            if self.is_valid_email(email):
                print(f"📧 Valid email found: {email}")
                return email
        
        # Method 2: Look for email labels
        label_patterns = [
            r'Email[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'email[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'Contact[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'E-mail[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'Mail[:\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
        ]
        
        for pattern in label_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and match:
                    email = match[0]
                else:
                    email = match
                
                if self.is_valid_email(email):
                    print(f"📧 Label email found: {email}")
                    return email
        
        print("❌ No valid email found in text")
        return "Email in CV"
    
    def enhanced_phone_extraction(self, text):
        """Enhanced phone extraction with better patterns"""
        # Multiple phone patterns
        phone_patterns = [
            r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # Standard US
            r'\+\d{1,3}[-.\s]?\d{1,14}',  # International
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Simple US
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # With parentheses
            r'Phone[:\s]*([+\d\s\-\(\)]{10,})',  # With Phone label
            r'phone[:\s]*([+\d\s\-\(\)]{10,})',  # With phone label
            r'Contact[:\s]*([+\d\s\-\(\)]{10,})',  # With Contact label
            r'Mobile[:\s]*([+\d\s\-\(\)]{10,})'  # With Mobile label
        ]
        
        for pattern in phone_patterns:
            try:
                matches = re.findall(pattern, text)
                for match in matches:
                    if isinstance(match, tuple) and match:
                        phone = match[0].strip()
                    else:
                        phone = match.strip()
                    
                    # Clean the phone number
                    phone = re.sub(r'[^\d+]', '', phone)
                    
                    if len(phone) >= 10:  # Valid phone should have at least 10 digits
                        print(f"📞 Phone found: {phone}")
                        return phone
            except Exception as e:
                print(f"⚠️ Phone pattern error: {e}")
                continue
        
        print("❌ No phone number found")
        return "Phone in CV"
    
    def enhanced_name_extraction(self, text):
        """Enhanced name extraction"""
        lines = text.split('\n')
        for line in lines[:10]:
            line_clean = line.strip()
            # Look for lines that might be names (not too long, no special keywords)
            if (len(line_clean) > 2 and len(line_clean) < 50 and
                not any(keyword in line_clean.lower() for keyword in 
                       ['email', 'phone', 'address', 'experience', 'education', 'skills', 'summary']) and
                re.match(r'^[A-Za-z\s\.\-]+$', line_clean)):
                return line_clean
        return "Candidate"
    
    def enhanced_location_extraction(self, text):
        """Enhanced location extraction"""
        location_patterns = [
            r'(\w+[\s\w]*),\s*(\w+[\s\w]*)',  # City, Country
            r'Location[:\s]*([^\n]+)',  # With Location label
            r'location[:\s]*([^\n]+)',  # With location label
            r'Address[:\s]*([^\n]+)',  # With Address label
            r'address[:\s]*([^\n]+)',  # With address label
            r'in\s+([A-Za-z\s]+(?:City|Town|Village))',  # "in London City"
            r'from\s+([A-Za-z\s]+)'  # "from Pakistan"
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and match:
                    location = match[0].strip()
                else:
                    location = match.strip()
                
                if location and len(location) > 2:
                    print(f"📍 Location found: {location}")
                    return location
        
        return "Location in CV"
    
    def enhanced_role_extraction(self, text):
        """Enhanced role extraction"""
        role_keywords = [
            'developer', 'engineer', 'manager', 'analyst', 'specialist', 
            'consultant', 'lead', 'architect', 'designer', 'programmer'
        ]
        
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in role_keywords) and len(line.strip()) < 50:
                return line.strip()
        
        return "Professional Role"
    
    def enhanced_experience_extraction(self, text):
        """Enhanced experience extraction"""
        exp_patterns = [
            r'(\d+)\s*(?:years?|yrs?)',
            r'Experience[:\s]*(\d+\s*(?:years?|yrs?))',
            r'experience[:\s]*(\d+\s*(?:years?|yrs?))',
            r'(\d+)\+?\s*years?'
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                years = match.group(1)
                return f"{years} years"
        
        return "Experience in CV"
    
    def enhanced_company_extraction(self, text):
        """Enhanced company extraction"""
        company_indicators = ['at', 'company', 'corporation', 'technologies', 'solutions', 'ltd', 'inc', 'gmbh']
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(indicator in line_lower for indicator in company_indicators):
                return line.strip()
        return "Company in CV"
    
    def enhanced_education_extraction(self, text):
        """Enhanced education extraction"""
        education_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'college', 'institute', 'bs', 'ms', 'mtech', 'btech']
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in education_keywords):
                return {
                    "highest_degree": line.strip(),
                    "university": "University in CV",
                    "graduation_year": "",
                    "qualifications": line.strip()
                }
        return {
            "highest_degree": "Education in CV",
            "university": "",
            "graduation_year": "",
            "qualifications": "Qualifications in CV"
        }
    
    def enhanced_skills_categorization(self, text):
        """Enhanced skills categorization"""
        text_lower = text.lower()
        
        programming_languages = []
        frameworks = []
        tools = []
        databases = []
        cloud_platforms = []
        
        # Programming Languages
        languages = ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'swift', 'kotlin', 'typescript']
        for lang in languages:
            if re.search(r'\b' + re.escape(lang) + r'\b', text_lower):
                programming_languages.append(lang.title())
        
        # Frameworks
        framework_list = ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'express', 'laravel', 'node.js']
        for framework in framework_list:
            if re.search(r'\b' + re.escape(framework) + r'\b', text_lower):
                frameworks.append(framework.title())
        
        # Databases
        database_list = ['mysql', 'mongodb', 'postgresql', 'oracle', 'sql server', 'redis', 'sqlite']
        for db in database_list:
            if re.search(r'\b' + re.escape(db) + r'\b', text_lower):
                databases.append(db.title())
        
        # Cloud Platforms
        cloud_list = ['aws', 'azure', 'google cloud', 'docker', 'kubernetes']
        for cloud in cloud_list:
            if re.search(r'\b' + re.escape(cloud) + r'\b', text_lower):
                cloud_platforms.append(cloud.title())
        
        # Tools
        tool_list = ['git', 'jenkins', 'jira', 'linux', 'windows', 'visual studio', 'eclipse']
        for tool in tool_list:
            if re.search(r'\b' + re.escape(tool) + r'\b', text_lower):
                tools.append(tool.title())
        
        return {
            "programming_languages": programming_languages,
            "frameworks": frameworks,
            "tools": tools,
            "databases": databases,
            "cloud_platforms": cloud_platforms
        }
    
    def is_valid_email(self, email):
        """Check if email is valid format"""
        if not email or not isinstance(email, str):
            return False
        
        # Basic email validation
        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        if not re.match(email_pattern, email):
            return False
        
        # Check for common domains
        valid_domains = ['.com', '.org', '.net', '.edu', '.in', '.co', '.io', '.ai', '.tech']
        if not any(domain in email.lower() for domain in valid_domains):
            return False
        
        return True