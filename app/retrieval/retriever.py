from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from langchain_core.documents import Document


class Retriever:

    def __init__(self, client, embedder):
        self.client = client
        self.embedder = embedder
        self.collection_name = "github_code"

    def retrieve(self, query, project_id, top_k=5, file_name=None):

        query_embedding = self.embedder.embed_query(query)

        conditions = [
            FieldCondition(
                key="project_id",
                match=MatchValue(value=project_id)
            )
        ]

        if file_name:
            conditions.append(
                FieldCondition(
                    key="file_name",
                    match=MatchValue(value=file_name)
                )
            )

        search_filter = Filter(
            must=conditions
        )

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            query_filter=search_filter,
            limit=top_k
        ).points

        documents = []

        for result in results:
            payload = result.payload

            documents.append(
                Document(
                    page_content=payload["code"],
                    metadata={
                        key: value
                        for key, value in payload.items()
                        if key != "code"
                    }
                )
            )

        return documents