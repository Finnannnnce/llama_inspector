from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from .routes import router

# Create the main app
app = FastAPI(
    title="SwackTech Analytics API",
    description="API for querying blockchain lending vault information",
    version="1.0.0",
    openapi_url=None,  # Disable default OpenAPI schema
    docs_url=None,  # Disable default docs URL
    redoc_url=None  # Disable default redoc URL
)

# Only enable HTTPS redirect in production (Cloud Run)
if not __debug__:  # __debug__ is False when running with -O flag in production
    app.add_middleware(HTTPSRedirectMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy"}

# Create API v1 router
api_v1 = APIRouter(prefix="/api/v1")

# Custom OpenAPI schema with proper server URL
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Set the server URL
    openapi_schema["servers"] = [
        {
            "url": "https://swacktech-api-330135650610.us-central1.run.app",
            "description": "Production server"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Documentation routes
@api_v1.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/api/v1/openapi.json",
        title=app.title + " - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )

@api_v1.get("/openapi.json", include_in_schema=False)
async def get_openapi_endpoint():
    return custom_openapi()

# Include API routes
api_v1.include_router(router)
app.include_router(api_v1)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "path": request.url.path}
    )

@app.exception_handler(500)
async def server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error"}
    )