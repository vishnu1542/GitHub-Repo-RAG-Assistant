from github_repo_loader.repo_loader import GitHubRepoLoader
from parser.parser import CodeParser
from chunker.chunker import CodeChunk
from embeddings.embedding import HuggingFaceEmbedder
from vector_store.vector_store import VectorStore
from retrieval.retriever import Retriever
from llm.assistance import CodeAssistant

from langchain_core.documents import Document


def main():

    repo_url = input("Enter GitHub repository URL: ")

    # -----------------------------
    # 1. Get repository
    # -----------------------------
    loader = GitHubRepoLoader()

    repo = loader.get_repositories(repo_url)

    project_id = f"{repo.owner.login}_{repo.name}"

    print(f"\nProject ID: {project_id}")


    # -----------------------------
    # 2. Connect to Vector DB
    # -----------------------------
    vector_store = VectorStore(vector_size=384)


    # -----------------------------
    # 3. Check repository exists
    # -----------------------------
    if vector_store.project_exists(project_id):

        print("Repository already exists in VectorDB.")
        print("Skipping loading, parsing, chunking and embedding.")

    else:

        print("Repository not found in VectorDB.")
        print("Processing repository...")

        # -----------------------------
        # 4. Load repository
        # -----------------------------
        files = loader.load_repository(repo)

        print(f"Loaded {len(files)} files")


        # -----------------------------
        # 5. Parse + Chunk
        # -----------------------------
        parser = CodeParser()
        chunker = CodeChunk()

        documents = []

        for file in files:

            language = file["language"]

            # Non-code files
            if language in ["json", "csv", "text", "markdown"]:

                document = parser.parse(
                    file["code"],
                    language,
                    file["file_name"],
                    file["path"]
                )

                if language == "json":

                    file_documents = chunker.chunk_json(document)

                elif language == "csv":

                    file_documents = chunker.chunk_csv(document)

                else:

                    file_documents = chunker.get_document_chunks(
                        document
                    )

                documents.extend(file_documents)


            # Code files
            else:

                tree, language, code, file_name, file_path = parser.parse(
                    file["code"],
                    language,
                    file["file_name"],
                    file["path"]
                )

                chunks = chunker.get_chunks(
                    tree.root_node,
                    code,
                    language,
                    file_name,
                    file_path
                )

                for chunk in chunks:

                    documents.append(
                        Document(
                            page_content=chunk["code"],
                            metadata={
                                "type": chunk["type"],
                                "language": chunk["language"],
                                "start_line": chunk["start_line"],
                                "end_line": chunk["end_line"],
                                "file_name": chunk["file_name"],
                                "file_path": chunk["file_path"]
                            }
                        )
                    )


        print(f"Created {len(documents)} chunks")


        # -----------------------------
        # 6. Create embeddings
        # -----------------------------
        embedder = HuggingFaceEmbedder()

        embeddings = embedder.embed_documents(documents)

        print(f"Created {len(embeddings)} embeddings")


        # -----------------------------
        # 7. Store in Qdrant
        # -----------------------------
        vector_store.store_embeddings(
            documents,
            embeddings,
            project_id
        )

        print("Repository stored in VectorDB.")


    # -----------------------------
    # 8. Create embedder
    # -----------------------------
    embedder = HuggingFaceEmbedder()


    # -----------------------------
    # 9. Create retriever
    # -----------------------------
    retriever = Retriever(
        vector_store.client,
        embedder
    )


    # -----------------------------
    # 10. Ask question
    # -----------------------------
    query = input("\nAsk a question about the repository: ")

    relevant_documents = retriever.retrieve(
        query,
        project_id,
        top_k=5
    )


    # -----------------------------
    # 11. Generate answer
    # -----------------------------
    assistant = CodeAssistant()

    answer = assistant.generate_answer(
        query,
        relevant_documents
    )

    print("\nAssistant:")
    print(answer)


if __name__ == "__main__":
    main()