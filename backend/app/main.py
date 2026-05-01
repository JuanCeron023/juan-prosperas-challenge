"""FastAPI application entry point.

Registers routers, exception handlers, and CORS middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.jobs.router import router as jobs_router
from app.stream.router import router as stream_router
from app.errors.handlers import register_exception_handlers

app = FastAPI(
    title="Async Report Processing API",
    description="Sistema de procesamiento asíncrono de reportes",
    version="1.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Register routers
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(stream_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Async Report Processing API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint that verifies DynamoDB and SQS connectivity."""
    from app.db.client import get_dynamodb_table
    from app.queue.client import get_sqs_client
    from app.config import settings
    from app.observability.metrics import metrics
    from fastapi.responses import JSONResponse

    dynamodb_status = "ok"
    sqs_status = "ok"

    # Check DynamoDB
    try:
        table = get_dynamodb_table(settings.dynamodb_jobs_table)
        table.table_status  # Triggers a DescribeTable call
    except Exception:
        dynamodb_status = "error"

    # Check SQS
    try:
        sqs = get_sqs_client()
        sqs.get_queue_attributes(
            QueueUrl=settings.sqs_standard_queue_url,
            AttributeNames=["ApproximateNumberOfMessages"],
        )
    except Exception:
        sqs_status = "error"

    status = "healthy" if dynamodb_status == "ok" and sqs_status == "ok" else "unhealthy"
    status_code = 200 if status == "healthy" else 503

    response = {
        "status": status,
        "dynamodb": dynamodb_status,
        "sqs": sqs_status,
        "metrics": metrics.to_dict(),
    }

    return JSONResponse(content=response, status_code=status_code)
