import os
import pickle
import json
import faiss
from sentence_transformers import SentenceTransformer

# Paths
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
PROMOTED_MODEL_PATH = os.path.join(MODELS_DIR, "promoted_model.pkl")
PIPELINE_PATH = os.path.join(MODELS_DIR, "pipeline.pkl")
METADATA_JSON_PATH = os.path.join(MODELS_DIR, "model_metadata.json")
INDEX_PATH = os.path.join(MODELS_DIR, "complaints_index.faiss")
COMPLAINTS_METADATA_PATH = os.path.join(MODELS_DIR, "complaints_metadata.json")

class ResourceCache:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ResourceCache, cls).__new__(cls, *args, **kwargs)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        self.ml_model = None
        self.pipeline = None
        self.model_metadata = {}
        self.faiss_index = None
        self.complaints_metadata = []
        self.initialized = True
        self.load_all()

    def load_all(self):
        # 1. Load ML Model & Pipeline
        if os.path.exists(PROMOTED_MODEL_PATH) and os.path.exists(PIPELINE_PATH):
            print("ResourceCache: Loading promoted ML model and pipeline...")
            with open(PROMOTED_MODEL_PATH, "rb") as f:
                self.ml_model = pickle.load(f)
            with open(PIPELINE_PATH, "rb") as f:
                self.pipeline = pickle.load(f)
        else:
            print("ResourceCache Warning: Promoted ML model or pipeline not found.")

        # 2. Load ML Metadata
        if os.path.exists(METADATA_JSON_PATH):
            with open(METADATA_JSON_PATH, "r") as f:
                self.model_metadata = json.load(f)
        else:
            print("ResourceCache Warning: model_metadata.json not found.")

        # 3. Load FAISS index & metadata
        if os.path.exists(INDEX_PATH) and os.path.exists(COMPLAINTS_METADATA_PATH):
            print("ResourceCache: Loading FAISS index and complaints metadata...")
            self.faiss_index = faiss.read_index(INDEX_PATH)
            with open(COMPLAINTS_METADATA_PATH, "r") as f:
                self.complaints_metadata = json.load(f)
        else:
            print("ResourceCache Warning: FAISS index or complaints metadata not found.")

    def reload(self):
        self.load_all()

def get_resources():
    return ResourceCache()
