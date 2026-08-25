import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "intfloat/multilingual-e5-base"
)


class EmbeddingService:
    """Singleton service for generating normalized dense vector embeddings."""

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def _load_model(self):
        if self._model is None:
            print(f"Loading SentenceTransformers model: {EMBEDDING_MODEL_NAME}...")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    def generate_embedding(self, text: str, is_query: bool = True) -> List[float]:
        """
        Generate a 768-dimensional normalized dense vector embedding.
        Prefixes string with 'query: ' for queries or 'passage: ' for index documents.
        """
        self._load_model()
        prefix = "query: " if is_query else "passage: "
        formatted_text = f"{prefix}{text.strip()}"
        
        vector = self._model.encode(formatted_text, normalize_embeddings=True)
        return vector.tolist()


# Global singleton instance
embedding_service = EmbeddingService()
