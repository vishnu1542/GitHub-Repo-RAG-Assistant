# GitHub Code Assistance

GitHub Code Assistance is a FastAPI-based RAG application that lets a user analyze a public GitHub repository and ask questions about its codebase through a modern chat interface.

The app preserves the existing RAG pipeline:

```text
GitHub Repository URL
    -> GitHubRepoLoader
    -> Repository files
    -> CodeParser
    -> CodeChunk
    -> LangChain Documents
    -> Hugging Face embeddings
    -> Qdrant collection: github_code
    -> Retriever filtered by project_id
    -> Gemini-powered CodeAssistant
    -> FastAPI response
    -> Frontend chat UI
```

## Features

- Analyze a public GitHub repository from a URL.
- Generate a stable `project_id` from repository owner and name.
- Store all repository chunks in one Qdrant collection named `github_code`.
- Skip duplicate indexing when the same `project_id` already exists in Qdrant.
- Retrieve answers only from the selected repository using `project_id`.
- Ask natural-language questions about the indexed code.
- Display assistant responses in a clean chat-style frontend.
- Show source file metadata when available.
- Keep all secrets on the backend.
- Serve frontend and backend from the same FastAPI app.

## Project Structure

```text
Github_code_assistance/
|
├── app/
│   ├── __init__.py
│   ├── main.py
│   |
│   ├── frontend/
│   │   ├── templates/
│   │   │   └── index.html
│   │   └── static/
│   │       ├── app.js
│   │       └── styles.css
│   |
│   ├── github_repo_loader/
│   │   ├── __init__.py
│   │   └── repo_loader.py
│   |
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── language.py
│   │   ├── parser.py
│   │   └── tree_utils.py
│   |
│   ├── chunker/
│   │   ├── __init__.py
│   │   └── chunker.py
│   |
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── embedding.py
│   |
│   ├── vector_store/
│   │   ├── __init__.py
│   │   └── vector_store.py
│   |
│   ├── retrieval/
│   │   ├── __init__.py
│   │   └── retriever.py
│   |
│   ├── llm/
│   │   ├── __init__.py
│   │   └── assistance.py
│   |
│   └── model/
│       ├── __int__.py
│       └── chunk.py
|
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Main Components

### FastAPI Backend

File: `app/main.py`

Responsibilities:

- Serves the frontend at `/`.
- Serves static files from `/static`.
- Exposes API routes for repository indexing and chat.
- Connects frontend requests to the existing RAG pipeline.
- Handles duplicate repository checks through Qdrant.
- Converts pipeline errors into user-friendly HTTP responses.

### GitHub Repository Loader

File: `app/github_repo_loader/repo_loader.py`

Responsibilities:

- Validates GitHub repository URLs.
- Uses `GITHUB_AUTH` to connect to GitHub.
- Loads supported files from public repositories.
- Ignores directories such as `.git`, `node_modules`, `venv`, `dist`, and `build`.

### Parser

Files:

- `app/parser/parser.py`
- `app/parser/language.py`

Responsibilities:

- Maps file extensions to supported languages.
- Uses Tree-sitter for supported code files.
- Creates LangChain `Document` objects for text-like files such as Markdown, JSON, CSV, and text.

### Chunker

File: `app/chunker/chunker.py`

Responsibilities:

- Splits parsed source code into class, method, and function chunks.
- Splits text/Markdown files with LangChain text splitters.
- Handles JSON and CSV chunking.

### Embeddings

File: `app/embeddings/embedding.py`

Responsibilities:

- Uses Hugging Face Inference API.
- Embedding model: `BAAI/bge-small-en-v1.5`.
- Supports `HF_TOKEN`.
- Also supports `HF_INFERENCE` as a fallback.

### Vector Store

File: `app/vector_store/vector_store.py`

Responsibilities:

- Connects to Qdrant Cloud.
- Uses one collection: `github_code`.
- Stores each chunk with metadata and `project_id`.
- Checks whether a repository already exists using `project_exists(project_id)`.
- Creates a payload index for `project_id`.

### Retriever

File: `app/retrieval/retriever.py`

Responsibilities:

- Embeds the user query.
- Searches Qdrant using a required `project_id` filter.
- Optionally supports filtering by file name.
- Returns LangChain `Document` objects.

### LLM Assistant

File: `app/llm/assistance.py`

Responsibilities:

- Uses Gemini through `langchain_google_genai`.
- Generates answers from retrieved repository context.
- Normalizes structured LLM responses into plain text for the API.

### Frontend

Files:

- `app/frontend/templates/index.html`
- `app/frontend/static/styles.css`
- `app/frontend/static/app.js`

Responsibilities:

- Provides a modern dark UI.
- Accepts a GitHub repository URL.
- Calls `/api/repository` to index or load an existing repository.
- Enables chat after repository readiness.
- Calls `/api/chat` for user questions.
- Displays assistant answers and source metadata.

## Environment Variables

Create a `.env` file in the project root.

```env
GITHUB_AUTH=your_github_token
HF_TOKEN=your_huggingface_token
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
GEMINI_API_KEY=your_gemini_api_key
```

Backward-compatible names supported by the code:

```env
HF_INFERENCE=your_huggingface_token
Qdrant_URL=your_qdrant_cloud_url
Qdrant_API_KEY=your_qdrant_api_key
```

Use the uppercase names for new deployments.

Do not expose these values in frontend JavaScript.

## Installation

Create and activate a virtual environment.

Windows:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run Locally

From the project root:

```bash
python -m app.main
```

The app starts at:

```text
http://127.0.0.1:8000
```

You can also run with Uvicorn directly:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## API Endpoints

### Health Check

```http
GET /api/health
```

Response:

```json
{
  "status": "ok",
  "app": "GitHub Code Assistance"
}
```

### Analyze Repository

```http
POST /api/repository
```

Request:

```json
{
  "repo_url": "https://github.com/owner/repository"
}
```

Response when repository is newly indexed:

```json
{
  "project_id": "owner_repository",
  "repository": "repository",
  "owner": "owner",
  "already_exists": false,
  "indexed_files": 24,
  "chunks": 120,
  "message": "Repository indexed successfully. You can start asking questions."
}
```

Response when repository already exists:

```json
{
  "project_id": "owner_repository",
  "repository": "repository",
  "owner": "owner",
  "already_exists": true,
  "indexed_files": 0,
  "chunks": 0,
  "message": "Repository already indexed. You can start asking questions."
}
```

### Chat

```http
POST /api/chat
```

Request:

```json
{
  "project_id": "owner_repository",
  "query": "How does authentication work?"
}
```

Response:

```json
{
  "answer": "Authentication is implemented in...",
  "sources": [
    {
      "file_name": "auth.py",
      "file_path": "app/auth.py",
      "start_line": 10,
      "end_line": 72
    }
  ]
}
```

## End-to-End Flow

1. User opens the app in the browser.
2. User enters a public GitHub repository URL.
3. Frontend sends the URL to `POST /api/repository`.
4. Backend validates the URL and loads the repository metadata.
5. Backend generates `project_id` from owner and repository name.
6. Backend checks Qdrant using `project_exists(project_id)`.
7. If the project already exists, backend skips loading, parsing, chunking, embedding, and storing.
8. If the project does not exist, backend loads supported repository files.
9. Parser parses code files with Tree-sitter and text-like files as documents.
10. Chunker creates LangChain documents.
11. Embedder creates Hugging Face embeddings.
12. Vector store writes chunks and metadata into Qdrant.
13. Frontend enables the chat UI.
14. User asks a question.
15. Frontend sends `project_id` and query to `POST /api/chat`.
16. Backend embeds the query.
17. Retriever searches Qdrant only inside the matching `project_id`.
18. Retrieved documents are passed to the LLM assistant.
19. Backend returns the final answer and sources.
20. Frontend displays the response in chat format.

## Supported File Types

The parser currently supports extensions configured in `app/parser/language.py`, including:

- `.py`
- `.java`
- `.js`
- `.ts`
- `.c`
- `.cpp`
- `.h`
- `.go`
- `.csv`
- `.txt`
- `.json`
- `.md`

## Error Handling

The backend handles common failures with friendly API responses:

- Invalid GitHub URL.
- Repository not found.
- Private or inaccessible repository.
- GitHub API errors.
- Empty repository.
- No supported files.
- No indexable chunks.
- Missing environment variables.
- Qdrant connection errors.
- Embedding errors.
- LLM errors.
- Invalid chat requests.

## Vercel Deployment

Vercel can deploy FastAPI apps through its Python runtime. This project keeps the FastAPI instance in `app/main.py`.

For Vercel detection, add this adapter file if it is not already present:

```python
# app/index.py
from app.main import app
```

Recommended `.vercelignore`:

```gitignore
venv/
__pycache__/
*.pyc
.ipynb_checkpoints/
practice.ipynb
app/practice2.ipynb
data/
.git/
.env
```

Set these environment variables in Vercel:

```env
GITHUB_AUTH=your_github_token
HF_TOKEN=your_huggingface_token
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
GEMINI_API_KEY=your_gemini_api_key
```

Deploy with:

```bash
npm i -g vercel
vercel login
vercel
```

Production deploy:

```bash
vercel --prod
```

Important: this app has heavier Python dependencies. Vercel serverless functions have bundle and execution-time limits, so large repositories may be better served on Render, Railway, Fly.io, or a VPS.

## Production Notes

- Keep `.env` out of source control.
- Use Qdrant Cloud for persistent vector storage.
- Use a GitHub token with only the permissions needed to read public repositories.
- Large repositories can take longer to parse, embed, and index.
- For heavy production usage, move repository indexing into a background job queue.
- Keep retrieval filtered by `project_id`; do not search across all repositories.
- Monitor Qdrant collection size and API usage.

## Troubleshooting

### Repository Error

Check that:

- The GitHub URL is public and valid.
- `GITHUB_AUTH` is set.
- The repository contains supported file types.
- Network access to GitHub is available.
- Qdrant credentials are correct.

### Qdrant Error

Check:

- `QDRANT_URL`
- `QDRANT_API_KEY`
- The Qdrant cluster status.
- Whether the collection `github_code` exists or can be created.

### Hugging Face Error

Check:

- `HF_TOKEN`
- Hugging Face account/API access.
- Access to model `BAAI/bge-small-en-v1.5`.

### Gemini Error

Check:

- `GEMINI_API_KEY`
- API access for the configured Gemini model.
- Quota and billing limits.

### Chat Response Validation Error

The assistant normalizes structured model responses into text before returning them. If this appears again, inspect the raw LLM response shape and update `CodeAssistant._content_to_text()`.

## Development Checks

Compile Python files:

```bash
python -m compileall app
```

Check health after starting the server:

```bash
curl http://127.0.0.1:8000/api/health
```

Expected:

```json
{"status":"ok","app":"GitHub Code Assistance"}
```

## Security

- The frontend never directly connects to GitHub, Qdrant, Hugging Face, or Gemini.
- All secrets stay on the backend.
- No login, signup, OAuth, JWT, or user account system is included.
- Public repository URLs are accepted; private repositories are not part of the intended flow.

## License

Add your preferred license here before publishing the project publicly.
