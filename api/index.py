from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
import threading
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dash-mmbu4l.example.com"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start_time
    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = str(max(elapsed, 0.0))
    return response

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-ce2lrkpj.apps.exam.local"

_lock = threading.Lock()
stats = {"total": 0, "valid": 0, "invalid": 0}


class VerifyRequest(BaseModel):
    token: str


@app.get("/")
def root():
    return {"ok": True}


@app.get("/stats")
def get_stats():
    with _lock:
        return {"total": stats["total"], "valid": stats["valid"], "invalid": stats["invalid"]}


@app.post("/verify")
def verify_token(body: VerifyRequest):
    try:
        payload = jwt.decode(
            body.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={"require": ["exp", "iss", "aud"]},
        )
        with _lock:
            stats["total"] += 1
            stats["valid"] += 1
        return {"valid": True, "email": payload.get("email"), "sub": payload.get("sub"), "aud": payload.get("aud")}
    except jwt.PyJWTError:
        with _lock:
            stats["total"] += 1
            stats["invalid"] += 1
        return JSONResponse(status_code=401, content={"valid": False})


handler = app
