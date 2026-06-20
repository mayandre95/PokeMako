from fastapi import FastAPI

app = FastAPI(title="PokéMako API")


@app.get("/health")
def health():
    return {"status": "ok"}
