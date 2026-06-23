import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(_API_KEY_HEADER)) -> str:
    expected = os.getenv("API_KEY", "")
    if not expected:
        raise HTTPException(
            status_code=500, detail="API_KEY non configurée côté serveur"
        )
    if api_key != expected:
        raise HTTPException(status_code=403, detail="API Key invalide ou absente")
    return api_key
