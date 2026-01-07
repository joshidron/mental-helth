import os
import pickle
import numpy as np
from docx import Document
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
from collections import Counter
import re

class LocalMentalHealthAI:
    def __init__(self, upload_folder='uploads', model_path='local_model.pkl'):
        self.upload_folder = upload_folder
        self.model_path = model_path
        # Load a small, fast local model for embeddings
        # all-MiniLM-L6-v2 is standard for speed/performance balance
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.knowledge_base = []
        self.embeddings = None
        self.knn = None
        self.labels = [] # Disease/Category labels corresponding to chunks
        
        self.load_model()

    def load_model(self):
        """Loads the trained data (embeddings + content) from disk."""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.knowledge_base = data['knowledge_base']
                self.embeddings = data['embeddings']
                self.labels = data['labels']
                # Re-fit KNN
                self.knn = NearestNeighbors(n_neighbors=3, metric='cosine')
                self.knn.fit(self.embeddings)
                return True
        return False

    def clean_text(self, text):
        return re.sub(r'\s+', ' ', text).strip()

    def extract_labeled_chunks_from_docx(self, file_path):
        """
        Heuristic Parser:
        Attempts to identify headings as 'Labels' (e.g. Anxiety, Depression)
        and associates the following paragraphs with that label.
        """
        doc = Document(file_path)
        chunks = []
        current_label = "General Mental Health"
        
        # Keywords to look for in headers to identify disjoint diseases
        disease_keywords = [
            "anxiety", "gad", "depression", "depressive", "ocd", "obsessive", 
            "stress", "burnout", "ptsd", "trauma", "adhd", "attention", 
            "autism", "personality", "eating", "food"
        ]

        current_chunk_text = []

        for para in doc.paragraphs:
            text = self.clean_text(para.text)
            if not text:
                continue

            # Check if this is a heading
            is_heading = False
            if para.style.name.startswith('Heading'):
                is_heading = True
            elif len(text) < 60 and any(k in text.lower() for k in disease_keywords):
                # Heuristic heading detection
                is_heading = True
            
            if is_heading:
                # Save previous chunk if it exists
                if current_chunk_text:
                    chunks.append({
                        "text": " ".join(current_chunk_text),
                        "label": current_label,
                        "source": os.path.basename(file_path)
                    })
                    current_chunk_text = []

                # Update label if it looks like a disease
                lower_text = text.lower()
                if any(k in lower_text for k in disease_keywords):
                    current_label = text
                
                # Treat the heading itself as part of the next chunk usually, 
                # but for labeling simplicity, we just set the label.
                # Use the heading as context for the next chunk
                current_chunk_text.append(text)
            else:
                current_chunk_text.append(text)
                
                # If chunk gets too big, split it
                if len(current_chunk_text) > 5: # approx 100-200 words
                     chunks.append({
                        "text": " ".join(current_chunk_text),
                        "label": current_label,
                        "source": os.path.basename(file_path)
                    })
                     current_chunk_text = []

        # Flush last chunk
        if current_chunk_text:
            chunks.append({
                 "text": " ".join(current_chunk_text),
                 "label": current_label,
                 "source": os.path.basename(file_path)
            })
            
        return chunks

    def train_model(self):
        """
        Ingests .docx files, chunks them, creates embeddings using local CPU model.
        """
        all_chunks = []
        
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)

        files = [f for f in os.listdir(self.upload_folder) if f.endswith('.docx')]
        if not files:
            return "No documents found."

        for f in files:
            path = os.path.join(self.upload_folder, f)
            chunks = self.extract_labeled_chunks_from_docx(path)
            all_chunks.extend(chunks)

        if not all_chunks:
            return "No content extracted."

        self.knowledge_base = all_chunks
        self.labels = [c['label'] for c in all_chunks]
        input_texts = [c['text'] for c in all_chunks]

        # Generate Embeddings (this runs locally on CPU)
        print("Generating embeddings... this may take a moment.")
        self.embeddings = self.encoder.encode(input_texts, show_progress_bar=True)
        
        # Train KNN
        self.knn = NearestNeighbors(n_neighbors=5, metric='cosine')
        self.knn.fit(self.embeddings)

        # Save
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'knowledge_base': self.knowledge_base,
                'embeddings': self.embeddings,
                'labels': self.labels
            }, f)

        return f"Training Complete. Processed {len(all_chunks)} chunks."

    def predict_disease(self, user_text):
        """
        Returns the most likely disease label based on semantic similarity.
        """
        if self.knn is None:
            if not self.load_model(): return "Model not trained."

        # Embed User Input
        user_vector = self.encoder.encode([user_text])
        
        # Find closest chunks
        distances, indices = self.knn.kneighbors(user_vector, n_neighbors=10)
        
        found_labels = []
        for idx in indices[0]:
            found_labels.append(self.labels[idx])
            
        # Return most common label
        most_common = Counter(found_labels).most_common(1)[0][0]
        return most_common
    
    def predict_top_diseases(self, user_text, top_n=3):
        """
        Returns top N disease predictions with confidence percentages.
        Confidence is calculated based on actual similarity scores (inverse of distances).
        Returns: [{'disease': 'GAD', 'confidence': 65.5}, ...]
        """
        if self.knn is None:
            if not self.load_model(): 
                return [{'disease': 'Model not trained', 'confidence': 0}]

        # Embed User Input
        user_vector = self.encoder.encode([user_text])
        
        # Find closest chunks (more neighbors for better statistics)
        distances, indices = self.knn.kneighbors(user_vector, n_neighbors=15)
        
        # Convert distances to similarity scores (inverse relationship)
        # Using exponential decay to emphasize closer matches
        # Add small epsilon to avoid division by zero
        epsilon = 1e-6
        similarities = np.exp(-distances[0])  # Exponential decay based on distance
        
        # Group similarities by disease label
        label_scores = {}
        for idx, similarity in zip(indices[0], similarities):
            label = self.labels[idx]
            if label not in label_scores:
                label_scores[label] = []
            label_scores[label].append(similarity)
        
        # Calculate weighted confidence for each disease
        # Use average similarity score for each disease
        disease_confidences = {}
        for label, scores in label_scores.items():
            # Average similarity score for this disease
            avg_score = np.mean(scores)
            # Weight by number of occurrences (more evidence = higher confidence)
            weighted_score = avg_score * (1 + 0.1 * len(scores))
            disease_confidences[label] = weighted_score
        
        # Normalize to percentages (sum to 100%)
        total_score = sum(disease_confidences.values())
        
        # Sort by confidence and get top N
        sorted_diseases = sorted(disease_confidences.items(), key=lambda x: x[1], reverse=True)
        
        predictions = []
        for label, score in sorted_diseases[:top_n]:
            confidence = (score / total_score) * 100
            predictions.append({
                'disease': label,
                'confidence': float(round(confidence, 1))  # Convert to native Python float for JSON serialization
            })
        
        return predictions

    def get_diagnosis(self, user_text):
        """
        Generates a text response based on retrieving relevant chunks.
        Since we have no LLM to generate sentences, we intelligently Select and Quote.
        """
        if self.knn is None:
            if not self.load_model(): return "Please ask the admin to Train the AI Model first."

        user_vector = self.encoder.encode([user_text])
        distances, indices = self.knn.kneighbors(user_vector, n_neighbors=3)

        response = "Based on your description, here is some relevant information from our database:\n\n"
        
        # Dedup chunks
        seen_text = set()
        
        for idx in indices[0]:
            chunk = self.knowledge_base[idx]
            text = chunk['text']
            label = chunk['label']
            
            # Simple dedup of exact text matches
            if text in seen_text: continue
            seen_text.add(text)
            
            response += f"**Relative to: {label}**\n"
            response += f"{text}\n\n"
            
        return response

    def generate_report_content(self, user_history_text):
        """
        Returns a JSON structure for the report using strictly retrieved content.
        """
        if self.knn is None:
             if not self.load_model(): return None

        predicted_disease = self.predict_disease(user_history_text)
        
        # Retrieve content SPECIFICALLY for this disease
        # We search specifically for the disease name + keywords like "advice", "diet", "myths"
        
        queries = {
            "Main Symptoms": f"{predicted_disease} symptoms main signs",
            "Actionable Advice": f"{predicted_disease} advice help tips coping",
            "Myths & Facts": f"{predicted_disease} myth fact misconception",
            "Diet & Routine": f"{predicted_disease} food diet daily routine"
        }
        
        report_structure = {
            f"Likely Assessment: {predicted_disease}": []
        }
        
        for section, query in queries.items():
            vec = self.encoder.encode([query])
            dist, idxs = self.knn.kneighbors(vec, n_neighbors=5)
            
            content_list = []
            seen_hashes = set()
            
            for i in idxs[0]:
                 # Safety check
                 if i >= len(self.knowledge_base): continue
                 
                 chunk_text = self.knowledge_base[i]['text']
                 
                 # 1. Filter out short garbage content (often just headers like "Main Symptoms")
                 # A real advice paragraph should be longer than 40-50 chars
                 if len(chunk_text) < 50:
                     continue
                     
                 # 2. Filter out duplicates
                 text_hash = hash(chunk_text)
                 if text_hash in seen_hashes:
                     continue
                 seen_hashes.add(text_hash)
                 
                 content_list.append(chunk_text)
                 
                 # Stop after getting 2 good items per section
                 if len(content_list) >= 2:
                     break
            
            # If nothing found (e.g. only short headers were found), fallback to something or just leave empty
            # If we leave it empty, the template might show a blank box.
            
            report_structure[f"Likely Assessment: {predicted_disease}"].append({
                "subtitle": section,
                "content": content_list
            })
            
        return report_structure

# Singleton
ai_engine = LocalMentalHealthAI()
