from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid

app = FastAPI()

ALLOWED_ORIGIN = "https://dash-mmbu4l.example.com"
EMAIL = "23f3002777@ds.study.iitm.ac.in"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_custom_headers(request: Request, call_next):
    start_time = time.perf_counter()
    request_id = str(uuid.uuid4())

    response = await call_next(request)

    process_time = time.perf_counter() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.6f}"

    return response

@app.get("/")
def home():
    return {"message": "FastAPI stats service is running"}

@app.get("/stats")
def stats(values: str = Query(...)):
    try:
        nums = [int(x.strip()) for x in values.split(",") if x.strip() != ""]
    except ValueError:
        raise HTTPException(status_code=400, detail="values must contain only integers")

    if not nums:
        raise HTTPException(status_code=400, detail="no values provided")

    total = sum(nums)
    count = len(nums)
    mean = total / count

    return {
        "email": EMAIL,
        "count": count,
        "sum": total,
        "min": min(nums),
        "max": max(nums),
        "mean": mean
    }