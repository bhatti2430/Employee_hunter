import re

class TextCleaner:
    def clean_text(self, text):
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:-]', '', text)
        return text.strip()
    
    def preprocess_for_ai(self, text):
        # Clean text for AI processing
        text = self.clean_text(text)
        # Limit length for API calls
        if len(text) > 4000:
            text = text[:4000] + "..."
        return text