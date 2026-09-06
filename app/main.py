from pathlib import Path
import os
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from github import GithubException, UnknownObjectException
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
DEAD_PROXY_VALUES = {"http://127.0.0.1:9", "https://127.0.0.1:9"}


def clear_dead_proxy_environment() -> None:
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        if os.getenv(key) in DEAD_PROXY_VALUES:
            os.environ.pop(key, None)


clear_dead_proxy_environment()

app = FastAPI(
    title="GitHub Code Assistance",
    description="Ask questions about public GitHub repositories using the existing RAG pipeline.",
    version="1.0.0",
)

templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))
app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR / "static")),
    name="static",
)


class RepositoryRequest(BaseModel):
    repo_url: str = Field(..., min_length=1)


class RepositoryResponse(BaseModel):
    project_id: str
    repository: str
    owner: str
    already_exists: bool
    indexed_files: int = 0
    chunks: int = 0
    message: str


class ChatRequest(BaseModel):
    project_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)


class Source(BaseModel):
    file_name: str | None = None
    file_path: str | None = None
    start_line: int | None = None
    end_line: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]


class HealthResponse(BaseModel):
    status: str
    app: str


def create_project_id(repo: Any) -> str:
    return f"{repo.owner.login}_{repo.name}"


def parse_and_chunk_files(files: list[dict[str, Any]]) -> list[Any]:
    from langchain_core.documents import Document

    from app.chunker.chunker import CodeChunk
    from app.parser.parser import CodeParser

    parser = CodeParser()
    chunker = CodeChunk()
    documents: list[Any] = []

    for file in files:
        language = file["language"]

        try:
            parsed = parser.parse(
                file["code"],
                language,
                file["file_name"],
                file["path"],
            )
        except ValueError:
            continue

        if language in ["json", "csv", "text", "markdown"]:
            if language == "json":
                file_documents = chunker.chunk_json(parsed)
            elif language == "csv":
                file_documents = chunker.chunk_csv(parsed)
            else:
                file_documents = chunker.get_document_chunks(parsed)

            documents.extend(file_documents)
            continue

        tree, language, code, file_name, file_path = parsed
        chunks = chunker.get_chunks(
            tree.root_node,
            code,
            language,
            file_name,
            file_path,
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
                        "file_path": chunk["file_path"],
                    },
                )
            )

    return documents


def index_repository(repo_url: str) -> RepositoryResponse:
    from app.embeddings.embedding import HuggingFaceEmbedder
    from app.github_repo_loader.repo_loader import GitHubRepoLoader
    from app.vector_store.vector_store import VectorStore

    try:
        loader = GitHubRepoLoader()
        repo = loader.get_repositories(repo_url)
        project_id = create_project_id(repo)
        vector_store = VectorStore(vector_size=384)

        if vector_store.project_exists(project_id):
            return RepositoryResponse(
                project_id=project_id,
                repository=repo.name,
                owner=repo.owner.login,
                already_exists=True,
                message="Repository already indexed. You can start asking questions.",
            )

        files = loader.load_repository(repo)
        if not files:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No supported files were found in this repository.",
            )

        documents = parse_and_chunk_files(files)
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No indexable code chunks were created from this repository.",
            )

        embedder = HuggingFaceEmbedder()
        embeddings = embedder.embed_documents(documents)
        vector_store.store_embeddings(documents, embeddings, project_id)

        return RepositoryResponse(
            project_id=project_id,
            repository=repo.name,
            owner=repo.owner.login,
            already_exists=False,
            indexed_files=len(files),
            chunks=len(documents),
            message="Repository indexed successfully. You can start asking questions.",
        )
    except UnknownObjectException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to access this repository. Check that the URL is correct and the repository is public.",
        ) from exc
    except GithubException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub returned an error while loading the repository.",
        ) from exc
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Repository indexing failed. Please check backend configuration and try again.",
        ) from exc


def source_from_document(document: Any) -> Source:
    metadata = document.metadata
    return Source(
        file_name=metadata.get("file_name"),
        file_path=metadata.get("file_path"),
        start_line=metadata.get("start_line"),
        end_line=metadata.get("end_line"),
    )


def answer_question(project_id: str, query: str) -> ChatResponse:
    from app.embeddings.embedding import HuggingFaceEmbedder
    from app.llm.assistance import CodeAssistant
    from app.retrieval.retriever import Retriever
    from app.vector_store.vector_store import VectorStore

    try:
        vector_store = VectorStore(vector_size=384)
        if not vector_store.project_exists(project_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository is not indexed yet. Analyze the repository first.",
            )

        embedder = HuggingFaceEmbedder()
        retriever = Retriever(vector_store.client, embedder)
        relevant_documents = retriever.retrieve(query, project_id, top_k=5)

        if not relevant_documents:
            return ChatResponse(
                answer="I could not find relevant code in this repository for that question.",
                sources=[],
            )

        assistant = CodeAssistant()
        answer = assistant.generate_answer(query, relevant_documents)

        seen_sources: set[tuple[Any, ...]] = set()
        sources: list[Source] = []
        for document in relevant_documents:
            source = source_from_document(document)
            source_key = (
                source.file_path,
                source.start_line,
                source.end_line,
            )
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources.append(source)

        return ChatResponse(answer=answer, sources=sources)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The assistant could not answer this question. Please try again.",
        ) from exc


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", app="GitHub Code Assistance")


@app.post("/api/repository", response_model=RepositoryResponse)
def create_repository(request: RepositoryRequest) -> RepositoryResponse:
    return index_repository(request.repo_url)


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return answer_question(request.project_id, request.query)


def main() -> None:
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
