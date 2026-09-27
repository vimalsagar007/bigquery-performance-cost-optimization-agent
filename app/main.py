import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router as main_router
from app.api.chat import chat_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("bq_agent.main")

app = FastAPI(
    title="BigQuery Performance and Cost Optimization Agent",
    description=(
        "AI-Powered production agent for analyzing BigQuery SQL queries, table metadata, "
        "INFORMATION_SCHEMA history, partitioning, clustering, and slot usage to deliver "
        "evidence-backed performance and cost optimization recommendations. Read-Only (V1)."
    ),
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(
        f"Path: {request.url.path} | Method: {request.method} | "
        f"Status: {response.status_code} | Duration: {duration:.4f}s"
    )
    return response


app.include_router(main_router)
app.include_router(chat_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
