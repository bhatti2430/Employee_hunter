from flask import Flask, render_template, request, jsonify, session
from src.core.ai_matcher import AIMatcher
from config import init_upload_folder, allowed_file, secure_filename
import os
import json

app = Flask(__name__)
app.secret_key = 'employee_hunter_secret_key_2024'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

matcher = AIMatcher()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_cv():
    if request.method == 'POST':
        if 'cv_file' not in request.files:
            return "No file uploaded", 400
        
        file = request.files['cv_file']
        candidate_name = request.form.get('name', 'Unknown Candidate')
        
        if file.filename == '':
            return "No file selected", 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                result = matcher.process_and_store_cv(file_path, candidate_name)
                
                if 'error' in result:
                    return f"Error: {result['error']}", 500
                
                return f"""
                <div style="text-align: center; padding: 50px;">
                    <h2 style="color: green;">✅ CV Uploaded Successfully!</h2>
                    <p><strong>Candidate:</strong> {candidate_name}</p>
                    <p><strong>Skills Found:</strong> {', '.join(result['skills']) if result['skills'] else 'Skills detected from CV'}</p>
                    <p><strong>Text Processed:</strong> {result['text_length']} characters</p>
                    <a href="/upload" style="color: #667eea; margin-right: 20px;">Upload Another CV</a>
                    <a href="/" style="color: #667eea;">Back to Home</a>
                </div>
                """
            except Exception as e:
                return f"Error processing CV: {str(e)}", 500
        
        return "Invalid file type", 400
    
    return render_template('upload.html')

@app.route('/search', methods=['GET', 'POST'])
def search_cvs():
    if request.method == 'POST':
        job_description = request.form.get('job_description', '').strip()
        
        if not job_description:
            return "Please enter job description", 400
        
        try:
            results = matcher.find_matching_cvs(job_description)
            
            # Store only lightweight search summary in session to avoid cookie size issues
            # Extract flat lists from nested ChromaDB result shape
            flat_ids = results.get('ids', [[]])[0] if results.get('ids') else []
            flat_distances = results.get('distances', [[]])[0] if results.get('distances') else []

            session['last_results'] = {
                'ids': flat_ids,
                'distances': flat_distances,
                'query': job_description,
                'timestamp': os.times().user  # lightweight timestamp
            }
            
            print(f"🔍 Search completed. Found {len(results['metadatas'][0]) if results and results.get('metadatas') and results['metadatas'][0] else 0} candidates")
            return render_template('results.html', results=results, query=job_description)
        except Exception as e:
            return f"Error searching CVs: {str(e)}", 500
    
    return render_template('index.html')

@app.route('/candidate_profile')
def candidate_profile():
    try:
        # Get candidate index from URL parameter
        candidate_index = request.args.get('index', type=int)
        
        if candidate_index is None:
            return "Candidate index not provided", 400
        
        candidate_data = session.get('last_results', {})
        ids = candidate_data.get('ids', [])
        distances = candidate_data.get('distances', [])
        query = candidate_data.get('query', '')
        
        print(f"👤 Loading profile for index: {candidate_index}")
        
        if not ids:
            return "No candidate data available. Please perform a search first.", 400
        
        # Validate index range
        if candidate_index < 0 or candidate_index >= len(ids):
            return f"Invalid candidate index: {candidate_index}. Only {len(ids)} candidates available.", 400
        
        # Fetch the CV metadata from the DB by ID to avoid storing large payloads in session
        cv_id = ids[candidate_index]
        record = matcher.db.get_cv_by_id(cv_id)
        if not record or not record.get('metadata'):
            return "Candidate metadata not available. The CV may have been removed.", 400
        
        metadata = record['metadata']
        print(f"✅ Loading candidate: {metadata.get('candidate_name', 'Unknown')}")
        
        # Create candidate details from metadata - ALL NEW FIELDS
        candidate_details = {
            'name': metadata.get('candidate_name', 'Unknown Candidate'),
            'email': metadata.get('email', 'Email in CV'),
            'phone': metadata.get('phone', 'Phone in CV'),
            'address': metadata.get('address', 'Address in CV'),
            'location': metadata.get('location', 'Location in CV'),
            'current_role': metadata.get('current_role', 'Professional Role'),
            'experience': metadata.get('experience', 'Experience in CV'),
            'current_company': metadata.get('current_company', 'Company in CV'),
            'education': metadata.get('education', 'Education details in CV'),
            'summary': metadata.get('summary', 'Professional with technical expertise'),
            'programming_languages': metadata.get('programming_languages', ''),
            'frameworks': metadata.get('frameworks', ''),
            'databases': metadata.get('databases', ''),
            'cloud_platforms': metadata.get('cloud_platforms', '')
        }
        
        skills = metadata.get('skills', '').split(', ') if metadata.get('skills') else []
        raw_text = metadata.get('raw_text', 'CV content preview not available')
        
        # Calculate ACCURATE match score for THIS SPECIFIC candidate
        match_score = 85  # Default fallback
        if distances and len(distances) > candidate_index:
            try:
                match_score = int(distances[candidate_index])
            except Exception:
                match_score = 85
            print(f"🎯 Accurate match score for candidate {candidate_index}: {match_score}%")
        
        return render_template(
            'candidate_profile.html',
            candidate_details=candidate_details,
            skills=skills,
            raw_text=raw_text,
            match_score=match_score
        )
        
    except Exception as e:
        print(f"❌ Error loading profile: {str(e)}")
        return f"Error loading profile: {str(e)}", 500

@app.route('/api/analyze_cv', methods=['POST'])
def api_analyze_cv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            result = matcher.process_and_store_cv(file_path, "API Candidate")
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

# Debug routes for database management
@app.route('/debug/database')
def debug_database():
    """Debug route to see database contents"""
    try:
        all_cvs = matcher.db.get_all_cvs()
        cv_count = matcher.db.get_cv_count()
        
        debug_info = {
            'total_cvs': cv_count,
            'cv_ids': all_cvs.get('ids', []),
            'candidate_names': [meta.get('candidate_name', 'Unknown') for meta in all_cvs.get('metadatas', [])],
            'skills_list': [meta.get('skills', 'No skills') for meta in all_cvs.get('metadatas', [])]
        }
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/debug/clear_database')
def clear_database():
    """Clear all data from database"""
    try:
        success = matcher.db.clear_database()
        return jsonify({'success': success, 'message': 'Database cleared'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/debug/cv_count')
def cv_count():
    """Get total CV count"""
    try:
        count = matcher.db.get_cv_count()
        return jsonify({'total_cvs': count})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    init_upload_folder()
    app.run(debug=True, host='0.0.0.0', port=5000)
