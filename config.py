import os
from dotenv import load_dotenv
import re
from unicodedata import normalize

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# LLM provider: 'openai' (default) or 'claude'
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

def init_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_filename(filename):
    filename = normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-zA-Z0-9._-]', '_', filename)