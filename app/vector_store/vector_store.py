import os
from uuid import uuid4
from qdrant_client.models import Filter, FieldCondition, MatchValue
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.models import PayloadSchemaType

load_dotenv()


class VectorStore:

    def __init__(self, vector_size):
        self.url = os.getenv("QDRANT_URL")
        self.api_key = os.getenv("QDRANT_API_KEY")

        if not self.url or not self.api_key:
            raise ValueError("QDRANT_URL or QDRANT_API_KEY not found")

        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key
        )

        self.collection_name = "github_code"

        self.create_collection(vector_size)

    def project_exists(self, project_id):
        result = self.client.count(
            collection_name=self.collection_name,
            count_filter=Filter(
                must=[
                    FieldCondition(
                        key="project_id",
                        match=MatchValue(value=project_id)
                    )
                ]
            )
        )

        return result.count > 0

    def create_collection(self, vector_size):

        collections = self.client.get_collections()

        exists = any(
            collection.name == self.collection_name
            for collection in collections.collections
        )

        if not exists:

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )

            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="project_id",
                field_schema=PayloadSchemaType.KEYWORD
            )

    def store_embeddings(self, documents, embeddings, project_id):

        points = []

        for document, embedding in zip(documents, embeddings):

            point = PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload={
                    **document.metadata,
                    "project_id": project_id,
                    "code": document.page_content
                }
            )

            points.append(point)

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )