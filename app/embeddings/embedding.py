import os

from dotenv import load_dotenv
from huggingface_hub import InferenceClient


load_dotenv()


class HuggingFaceEmbedder:

    def __init__(self):

        token = os.getenv("HF_INFERENCE")

        if not token:
            raise ValueError("HF_TOKEN not found")

        self.client = InferenceClient(
            provider="hf-inference",
            api_key=token
        )

        self.model = "BAAI/bge-small-en-v1.5"

    def embed_query(self, query):
        return self.client.feature_extraction(
            query,
            model=self.model
        )
    def embed_documents(self, documents):

        texts = [
            document.page_content
            for document in documents
        ]

        embeddings = self.client.feature_extraction(
            texts,
            model=self.model
        )

        return embeddings
