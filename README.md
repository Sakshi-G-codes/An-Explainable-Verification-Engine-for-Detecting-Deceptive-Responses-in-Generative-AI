# Explainable Healthcare Verification Engine

An advanced, full-stack AI pipeline designed to detect and mitigate Large Language Model (LLM) hallucinations in the medical domain. The system extracts atomic claims from AI-generated text, cross-references them against a trusted medical knowledge base using hybrid retrieval, and employs a Natural Language Inference (NLI) model to classify each claim's veracity.

## 🚀 Key Features

*   **Hybrid Knowledge Retrieval**: Combines Dense (FAISS + MedCPT) and Sparse (BM25) vector retrieval using Reciprocal Rank Fusion (RRF) to find the most accurate ground-truth evidence.
*   **Similarity Gating**: Bypasses heavy NLI computation and flags claims as `UNVERIFIED` if the vector similarity of retrieved facts falls below 0.65.
*   **NLI Text Classification**: Uses Microsoft's `cross-encoder/nli-deberta-v3-base` to semantically classify claims as `VERIFIED`, `CONTRADICTORY`, or `UNVERIFIED`.
*   **In-Memory Caching**: Caches retrieval and NLI inferences to provide instant 0ms responses for recurring claims.
*   **Explainable UI**: A React dashboard that visually color-codes sentences and provides an interactive "Explanation Drawer" exposing the exact retrieved evidence and confidence scores.

---

## 🛠️ Technology Stack

**Frontend:**
*   React 18 + Vite
*   TypeScript
*   Tailwind CSS v4
*   Axios & Lucide React

**Backend:**
*   Python 3.13, Django 6.1, Django REST Framework
*   **NLP & ML Engine**: `spaCy`, `SentenceTransformers`, `PyTorch`
*   **Embedding Model**: `ncbi/MedCPT-Article-Encoder` (Biomedical domain)
*   **Vector Database**: `faiss-cpu` (Dense) and `rank_bm25` (Sparse)
*   **NLI Model**: `cross-encoder/nli-deberta-v3-base`

---

## 💻 Setup & Installation Guide (For Any Machine)

### Prerequisites
*   **Python 3.10+** installed
*   **Node.js 18+** installed
*   Git (if cloning the repository)

### 1. Backend Setup

Open a terminal and navigate to the project root, then into the `backend` folder:

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install rank_bm25

# Download the spaCy English model (used for sentence/claim extraction)
python -m spacy download en_core_web_sm

# Apply Django migrations (initial setup)
python manage.py migrate
```

### 2. Build the Knowledge Base Index

Before starting the server, you must build the FAISS and BM25 databases. This parses the local medical facts and converts them into searchable embeddings.

```bash
python manage.py build_index
```
*(Note: The first time you run this, it will download the `MedCPT` embedding model from Hugging Face (~300MB).)*

### 3. Frontend Setup

Open a **new, second terminal window**, navigate to the project root, and go into the `frontend` folder:

```bash
cd frontend

# Install Node modules
npm install
```

---

## 🏃‍♂️ Execution Guide

To run the application, you must start both the backend and frontend servers simultaneously.

**Terminal 1 (Backend):**
```bash
cd backend
# Activate virtual environment first
.\venv\Scripts\activate    # (or source venv/bin/activate)
python manage.py runserver
```
*The backend API will run on `http://127.0.0.1:8000`.*

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```
*The frontend UI will run on `http://localhost:5173`.*

---

## 💡 Usage Instructions

1. Open your browser and navigate to the frontend URL (e.g., `http://localhost:5173`).
2. **Manual Mode**: Type a medical query and paste an AI response, then click **Verify Response**.
3. **Auto Mode**: Type a keyword (like `"aspirin"`, `"vaccine"`, or `"cancer"`) in the query box and click **Auto-Generate & Verify**. The backend will mock a generated LLM response and instantly verify it.
4. **Explanation**: The text will be highlighted in Green, Amber, or Red. Click on any highlighted sentence to open the **Explanation Drawer** at the bottom, which reveals the exact medical evidence used to classify that sentence!

*(Note: The very first time you verify a response, the system will pause to download the `DeBERTa` cross-encoder model (~700MB). All subsequent verifications will be lightning-fast due to caching).*
