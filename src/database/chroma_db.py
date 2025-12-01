import chromadb
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import uuid
import os

class ChromaDB:
    def __init__(self):
        try:
            # Create data directory if it doesn't exist
            data_dir = "./cv_database"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # Use PersistentClient for permanent storage
            self.client = chromadb.PersistentClient(path=data_dir)
            self.collection = self.client.get_or_create_collection("employee_cvs")
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            print("✅ ChromaDB PersistentClient initialized - Data will be saved")
        except Exception as e:
            print(f"❌ ChromaDB init failed: {e}")
            # Fallback to EphemeralClient
            try:
                self.client = chromadb.EphemeralClient()
                self.collection = self.client.create_collection("employee_cvs")
                self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
                print("⚠️ Using EphemeralClient (data will be lost on restart)")
            except:
                raise Exception("Database initialization failed")
        
    def add_cv(self, text, metadata):
        try:
            cv_id = str(uuid.uuid4())
            
            safe_metadata = {}
            for key, value in metadata.items():
                safe_metadata[key] = str(value)
            
            self.collection.add(
                documents=[text],
                metadatas=[safe_metadata],
                ids=[cv_id]
            )
            print(f"✅ CV stored permanently: {metadata['candidate_name']}")
            return cv_id
            
        except Exception as e:
            print(f"❌ Failed to store CV: {e}")
            raise Exception(f"Database storage failed: {str(e)}")
    
    def search_similar(self, query, n_results=5):
        try:
            all_docs = self.collection.get()
            
            print(f"📊 Database contains: {len(all_docs['documents'])} CVs")
            
            if not all_docs['documents']:
                print("❌ No CVs found in database")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]], 'ids': [[]]}
            
            documents = all_docs['documents']
            metadatas = all_docs['metadatas']
            ids = all_docs['ids']
            
            print(f"🔍 Searching for: '{query[:50]}...'")
            
            # Use TF-IDF for similarity matching
            all_texts = documents + [query]
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            
            doc_vectors = tfidf_matrix[:-1]
            query_vector = tfidf_matrix[-1]
            
            # Calculate cosine similarities
            similarities = cosine_similarity(query_vector, doc_vectors).flatten()
            
            # Filter out very low similarities (below threshold) - STRICTER FILTERING
            threshold = 0.15  # Increased threshold to 15% for better matches
            valid_indices = [i for i, sim in enumerate(similarities) if sim > threshold]
            
            if not valid_indices:
                print("❌ No meaningful matches found")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]], 'ids': [[]]}
            
            # Get top N results from valid matches
            valid_similarities = [similarities[i] for i in valid_indices]
            top_indices = [valid_indices[i] for i in np.argsort(valid_similarities)[::-1][:n_results]]
            
            result_documents = [documents[i] for i in top_indices]
            result_metadatas = [metadatas[i] for i in top_indices]
            result_ids = [ids[i] for i in top_indices]
            
            # Convert to realistic percentage scores (only for meaningful matches)
            result_scores = []
            for sim in [similarities[i] for i in top_indices]:
                score = 65 + (sim * 30)  # Map to 65-95% (more realistic range)
                score = max(65, min(95, int(score)))
                result_scores.append(score)
            
            print(f"🎯 Found {len(top_indices)} meaningful matches with scores: {result_scores}")
            
            for i, (metadata, score, cv_id) in enumerate(zip(result_metadatas, result_scores, result_ids)):
                candidate_name = metadata.get('candidate_name', 'Unknown')
                skills = metadata.get('skills', 'No skills')
                print(f"   {i+1}. {candidate_name} - {score}% - ID: {cv_id}")
            
            return {
                'documents': [result_documents],
                'metadatas': [result_metadatas],
                'distances': [result_scores],
                'ids': [result_ids]  # Include IDs for proper mapping
            }
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]], 'ids': [[]]}
    
    def get_all_cvs(self):
        try:
            all_docs = self.collection.get()
            return all_docs
        except Exception as e:
            print(f"❌ Failed to get all CVs: {e}")
            return {'documents': [], 'metadatas': [], 'ids': []}
    
    def get_cv_count(self):
        try:
            all_docs = self.collection.get()
            return len(all_docs['documents'])
        except Exception as e:
            print(f"❌ Failed to get CV count: {e}")
            return 0

    def get_cv_by_id(self, cv_id):
        """Retrieve a single CV's document and metadata by its ID."""
        try:
            doc = self.collection.get(ids=[cv_id])
            # chroma's get returns lists; ensure we have content
            if doc and doc.get('ids'):
                return {
                    'id': doc['ids'][0],
                    'document': doc['documents'][0] if doc.get('documents') else '',
                    'metadata': doc['metadatas'][0] if doc.get('metadatas') else {}
                }
            return None
        except Exception as e:
            print(f"❌ Failed to get CV by id {cv_id}: {e}")
            return None
    
    def delete_cv(self, cv_id):
        try:
            self.collection.delete(ids=[cv_id])
            print(f"✅ CV deleted: {cv_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to delete CV: {e}")
            return False
    
    def clear_database(self):
        try:
            all_docs = self.collection.get()
            if all_docs['ids']:
                self.collection.delete(ids=all_docs['ids'])
                print("✅ Database cleared successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to clear database: {e}")
            return False