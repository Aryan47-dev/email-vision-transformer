from fastapi import FastAPI

app = FastAPI(title="Email Vision Transformer API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
