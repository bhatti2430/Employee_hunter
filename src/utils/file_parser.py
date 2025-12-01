import PyPDF2
import docx2txt
import os
import pdfplumber
import re

class CVParser:
    def extract_text_from_pdf(self, file_path):
        text = ""
        print(f"📄 Reading PDF: {file_path}")
        
        try:
            # Method 1: Try pdfplumber first (better for complex PDFs)
            print("🔧 Trying pdfplumber...")
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text += page_text + "\n"
                            print(f"   📄 Page {i+1}: {len(page_text)} characters")
                    except Exception as e:
                        print(f"   ❌ Page {i+1} error: {e}")
                        continue
            
            if text.strip():
                print(f"✅ pdfplumber extracted {len(text)} characters")
                return text
                
        except Exception as e:
            print(f"❌ pdfplumber failed: {e}")
        
        try:
            # Method 2: Try PyPDF2
            print("🔧 Trying PyPDF2...")
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for i, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text += page_text + "\n"
                            print(f"   📄 Page {i+1}: {len(page_text)} characters")
                    except Exception as e:
                        print(f"   ❌ Page {i+1} error: {e}")
                        continue
            
            if text.strip():
                print(f"✅ PyPDF2 extracted {len(text)} characters")
                return text
                
        except Exception as e:
            print(f"❌ PyPDF2 failed: {e}")
        
        # Method 3: If both fail, try to extract any readable text
        print("🔧 Trying raw text extraction...")
        try:
            with open(file_path, 'rb') as file:
                raw_content = file.read()
                # Try to extract text between parentheses and other patterns
                text_matches = re.findall(b'[\\x20-\\x7E]{10,}', raw_content)
                if text_matches:
                    text = b' '.join(text_matches).decode('latin-1', errors='ignore')
                    print(f"✅ Raw extraction got {len(text)} characters")
                    return text
        except Exception as e:
            print(f"❌ Raw extraction failed: {e}")
        
        return "PDF text extraction failed - file may be scanned or corrupted"
    
    def extract_text_from_docx(self, file_path):
        try:
            text = docx2txt.process(file_path)
            if text.strip():
                print(f"✅ DOCX extracted {len(text)} characters")
                return text
            return "DOCX file is empty"
        except Exception as e:
            return f"DOCX extraction error: {str(e)}"
    
    def extract_text_from_txt(self, file_path):
        try:
            encodings = ['utf-8', 'latin-1', 'windows-1252', 'cp1252']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        text = file.read()
                        if text.strip():
                            print(f"✅ TXT extracted {len(text)} characters with {encoding}")
                            return text
                except UnicodeDecodeError:
                    continue
            return "Could not read TXT file with any encoding"
        except Exception as e:
            return f"TXT extraction error: {str(e)}"
    
    def parse_cv(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        print(f"📁 Processing {ext.upper()} file: {os.path.basename(file_path)}")
        
        if ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return self.extract_text_from_docx(file_path)
        elif ext == '.txt':
            return self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")