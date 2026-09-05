import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from dotenv import load_dotenv

load_dotenv()


class VectorStore:

    def __init__(self):
        self.url = os.getenv("QDRANT_URL")
        self.api_key = os.getenv("QDRANT_API_KEY")

        if not self.url or not self.api_key:
            raise ValueError("QDRANT_URL or QDRANT_API_KEY not found")

        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key
        )

        self.collection_name = "github_code"

    def store_embeddings(self, documents, embeddings, project_id):

        points = []

        for i, (document, embedding) in enumerate(
            zip(documents, embeddings)
        ):

            points.append(
                PointStruct(
                    id=i,
                    vector=embedding,
                    payload={
                        **document.metadata,
                        "project_id": project_id,
                        "code": document.page_content
                    }
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )