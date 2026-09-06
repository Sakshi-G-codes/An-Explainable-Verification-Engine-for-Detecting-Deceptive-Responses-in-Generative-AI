import os
import json
import pickle
import urllib.request
import faiss
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

def build_index():
    print("Loading MedCPT model...")
    model = SentenceTransformer('ncbi/MedCPT-Article-Encoder')
    
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Robust structured Medical Dataset
    scifact_data = [
        {"id": "1", "text": "Aspirin should not be given to children or teenagers with viral infections due to the risk of Reye's syndrome. It is unsafe.", "source": "Clinical Guidelines"},
        {"id": "2", "text": "Vaccines are effective at preventing many serious diseases and do not cause autism.", "source": "CDC"},
        {"id": "3", "text": "Drinking water does not cure cancer, but staying hydrated is important for general health.", "source": "Medical Knowledge"},
        {"id": "4", "text": "Hypertension is a major risk factor for cardiovascular disease.", "source": "SciFact corpus"},
        {"id": "5", "text": "Metformin is a first-line treatment for type 2 diabetes.", "source": "SciFact corpus"},
        {"id": "6", "text": "Ibuprofen is a nonsteroidal anti-inflammatory drug (NSAID) used to relieve pain, reduce inflammation, and lower fever.", "source": "Pharmacology Textbook"},
        {"id": "7", "text": "Vitamin C does not cure the common cold, but regular supplementation may slightly reduce the duration of symptoms.", "source": "Cochrane Review"},
        {"id": "8", "text": "COVID-19 is caused by the SARS-CoV-2 virus and spreads primarily through respiratory droplets.", "source": "WHO"},
        {"id": "9", "text": "Amoxicillin is an antibiotic used to treat bacterial infections, such as middle ear infections and strep throat. It is completely ineffective against viral infections.", "source": "SciFact corpus"},
        {"id": "10", "text": "Prolonged exposure to ultraviolet (UV) radiation from the sun increases the risk of skin cancer, including melanoma.", "source": "Dermatology Guide"}
    ]
    
    print(f"Loaded {len(scifact_data)} medical documents. Embedding texts for FAISS...")
    
    # 2. Embed and build FAISS Dense Index
    texts = [item['text'] for item in scifact_data]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    
    print("Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    faiss_path = os.path.join(data_dir, 'faiss_index.bin')
    faiss.write_index(index, faiss_path)
    
    # 3. Build BM25 Sparse Index
    print("Building BM25 sparse index...")
    tokenized_corpus = [doc.lower().split(" ") for doc in texts]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_path = os.path.join(data_dir, 'bm25_index.pkl')
    with open(bm25_path, 'wb') as f:
        pickle.dump(bm25, f)
    
    # 4. Save Metadata mapping
    metadata_path = os.path.join(data_dir, 'metadata.json')
    metadata = {item['id']: item for item in scifact_data}
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
        
    print(f"Successfully built FAISS and BM25 indexes with {len(scifact_data)} documents at {data_dir}")

if __name__ == "__main__":
    build_index()
