from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import uvicorn

app = FastAPI()
model = SentenceTransformer('all-MiniLM-L6-v2')

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/gpu-status")
async def gpu_status():
    return {
        "gpu_available": False,
        "gpu_memory_available": 0,
        "gpu_memory_total": 0
    }

@app.post("/encoder/bi-encoder-embed")
async def embed(data: dict):
    texts = data.get("texts", [])
    embeddings = model.encode(texts)
    return {"embeddings": embeddings.tolist()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
