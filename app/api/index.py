from fastapi import FastAPI

app = FastAPI()


@app.get("/api")
def root():
    return {
        "message": "GitHub Repo RAG Assistant API is running"
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok"
    }