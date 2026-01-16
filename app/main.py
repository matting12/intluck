from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

import logging


from app.api.routes_autocomplete import router as autocomplete_router
from app.api.routes_company import router as company_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Job Matching API")


# Add cache control middleware for static files
class NoCacheStaticMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheStaticMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info("FastAPI server starting up")
    logger.info("Endpoints:")
    logger.info("  - /api/autocomplete/job-title")
    logger.info("  - /api/autocomplete/company")
    logger.info("  - /api/company-info")
    logger.info("  - /api/salary-benefits")
    logger.info("  - /api/company-reviews")
    logger.info("  - /api/interview-prep")
    logger.info("=" * 50)

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

app.include_router(autocomplete_router, prefix="/api/autocomplete")
app.include_router(company_router, prefix="/api")