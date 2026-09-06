import os
import json
import pickle
import faiss
import spacy
import torch
from sentence_transformers import SentenceTransformer, CrossEncoder

class VerificationEngine:
    def __init__(self):
        print("Initializing Verification Engine...")
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        
        # Load NLP models
        print("Loading biomedical NLP models...")
        try:
            self.nlp = spacy.load('en_core_sci_md')
        except OSError:
            try:
                from spacy.cli import download
                download('en_core_sci_md')
                self.nlp = spacy.load('en_core_sci_md')
            except BaseException as e:
                print(f"Failed to load scispacy en_core_sci_md: {e}. Falling back to en_core_web_sm.")
                self.nlp = spacy.load('en_core_web_sm')

        self.retriever = SentenceTransformer('ncbi/MedCPT-Article-Encoder')
        self.nli_model = CrossEncoder('cross-encoder/nli-deberta-v3-base')
        
        # Caching layer to speed up redundant claim processing
        self.retrieval_cache = {}
        self.nli_cache = {}
        
        # Map labels dynamically in case model config varies
        self.label_mapping = self.nli_model.config.id2label
        self.contradiction_idx = next((k for k, v in self.label_mapping.items() if 'contradiction' in v.lower()), 0)
        self.entailment_idx = next((k for k, v in self.label_mapping.items() if 'entailment' in v.lower()), 1)
        
        # Load Indexes
        self.index = faiss.read_index(os.path.join(self.data_dir, 'faiss_index.bin'))
        with open(os.path.join(self.data_dir, 'bm25_index.pkl'), 'rb') as f:
            self.bm25 = pickle.load(f)
            
        with open(os.path.join(self.data_dir, 'metadata.json'), 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)

    def extract_claims(self, text):
        doc = self.nlp(text)
        return [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 5]

    def retrieve_hybrid(self, claim, top_k=3):
        if claim in self.retrieval_cache:
            return self.retrieval_cache[claim]
            
        # 1. FAISS Dense Retrieval
        embedding = self.retriever.encode([claim], normalize_embeddings=True)
        distances, indices = self.index.search(embedding, top_k * 2) # Get more for RRF
        
        faiss_ranks = {}
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx != -1:
                faiss_ranks[str(idx)] = {"rank": rank, "score": float(dist)}
                
        # 2. BM25 Sparse Retrieval
        tokenized_query = claim.lower().split(" ")
        bm25_scores = self.bm25.get_scores(tokenized_query)
        bm25_top_indices = bm25_scores.argsort()[::-1][:top_k * 2]
        
        bm25_ranks = {}
        for rank, idx in enumerate(bm25_top_indices):
            bm25_ranks[str(idx)] = {"rank": rank, "score": float(bm25_scores[idx])}
            
        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        all_ids = set(faiss_ranks.keys()).union(set(bm25_ranks.keys()))
        k_rrf = 60
        
        for doc_id in all_ids:
            score = 0.0
            if doc_id in faiss_ranks:
                score += 1.0 / (k_rrf + faiss_ranks[doc_id]["rank"])
            if doc_id in bm25_ranks:
                score += 1.0 / (k_rrf + bm25_ranks[doc_id]["rank"])
            rrf_scores[doc_id] = score
            
        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_k]
        
        evidence = []
        for doc_id in sorted_ids:
            if doc_id in self.metadata:
                meta = self.metadata[doc_id]
                faiss_score = faiss_ranks.get(doc_id, {}).get("score", 0.0)
                evidence.append({
                    "text": meta['text'],
                    "source": meta['source'],
                    "faiss_similarity": faiss_score,
                    "rrf_score": rrf_scores[doc_id]
                })
                
        self.retrieval_cache[claim] = evidence
        return evidence

    def verify(self, query, response_text):
        claims = self.extract_claims(response_text)
        results = []
        verified_count = 0
        contradictory_count = 0

        for claim in claims:
            evidence_list = self.retrieve_hybrid(claim, top_k=3)
            
            # Similarity Gating
            top_faiss_score = max([ev['faiss_similarity'] for ev in evidence_list]) if evidence_list else 0.0
            
            if top_faiss_score < 0.65:
                results.append({
                    "text": claim,
                    "status": "UNVERIFIED",
                    "reason": "Insufficient Knowledge Base Evidence",
                    "confidence": 0.0,
                    "evidence": evidence_list
                })
                continue
                
            # NLI Multi-evidence aggregation
            has_contradiction = False
            has_entailment = False
            max_contradiction_prob = 0.0
            max_entailment_prob = 0.0
            
            for ev in evidence_list:
                cache_key = f"{ev['text']}|||{claim}"
                
                if cache_key in self.nli_cache:
                    probs = self.nli_cache[cache_key]
                else:
                    scores = self.nli_model.predict([(ev['text'], claim)])[0]
                    probs = torch.softmax(torch.tensor(scores), dim=-1).tolist()
                    self.nli_cache[cache_key] = probs
                
                contra_prob = probs[self.contradiction_idx]
                entail_prob = probs[self.entailment_idx]
                
                if contra_prob > max_contradiction_prob:
                    max_contradiction_prob = contra_prob
                if entail_prob > max_entailment_prob:
                    max_entailment_prob = entail_prob
                    
                if contra_prob > 0.85:
                    has_contradiction = True
                if entail_prob > 0.80:
                    has_entailment = True

            if has_contradiction:
                status = "CONTRADICTORY"
                confidence = max_contradiction_prob
                contradictory_count += 1
            elif has_entailment:
                status = "VERIFIED"
                confidence = max_entailment_prob
                verified_count += 1
            else:
                status = "UNVERIFIED"
                confidence = max(max_contradiction_prob, max_entailment_prob)
                
            results.append({
                "text": claim,
                "status": status,
                "confidence": confidence,
                "evidence": evidence_list
            })

        total = len(claims)
        if total > 0:
            trust_score = max(0, min(100, (verified_count * 100 - contradictory_count * 100) / total))
            if verified_count == 0 and contradictory_count == 0:
                trust_score = 50.0
        else:
            trust_score = 100.0

        return {
            "query": query,
            "raw_response": response_text,
            "claims": results,
            "trust_score": trust_score
        }

engine_instance = None
def get_engine():
    global engine_instance
    if engine_instance is None:
        engine_instance = VerificationEngine()
    return engine_instance
