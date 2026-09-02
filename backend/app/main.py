from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.health import router as health_router
from app.api.suggest import router as suggest_router
from app.api.execute import router as execute_router
from app.api.reference import router as reference_router
from app.api.templates import router as templates_router
from app.api.agent import router as agent_router
from app.api.chat import router as chat_router
from app.retrieval.embedder import embedding_service




@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load ML embedding model on server startup."""
    print("Pre-loading SentenceTransformers embedding model...")
    embedding_service._load_model()
    print("Embedding model successfully loaded.")
    yield


app = FastAPI(
    title="PMC Officer Query System API",
    description="Controlled Natural Language Query Interface for PMC Complaint Analytics",
    version="1.0.0-poc",
    lifespan=lifespan
)

# Enable CORS for local and network frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_origin_regex=r"http://.*:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.mcp.server import mcp_server

app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(suggest_router, prefix="/api", tags=["Retrieval"])
app.include_router(execute_router, prefix="/api", tags=["Execution"])
app.include_router(reference_router, prefix="/api", tags=["Reference Options"])
app.include_router(templates_router, prefix="/api", tags=["Developer Templates"])
app.include_router(agent_router, prefix="/api", tags=["Gemini Agent Mode"])
app.include_router(chat_router, prefix="/api", tags=["Chat History & Multi-Chat"])

# Mount Official Model Context Protocol (MCP) Server over SSE / JSON-RPC
app.mount("/mcp", mcp_server.http_app())

# Mount Vanna AI 2.0 Agent Routes (/api/vanna/v2/chat_sse, chat_poll, chat_websocket)
try:
    from vanna.servers.fastapi.routes import register_chat_routes
    from vanna.servers.base import ChatHandler
    from app.vanna_agent import vanna_agent
    chat_handler = ChatHandler(vanna_agent)
    register_chat_routes(app, chat_handler)
    print("Successfully mounted Vanna AI 2.0 endpoints.")
except Exception as e:
    print(f"Warning: Could not mount Vanna AI routes: {e}")







@app.get("/")
def root():
    return {
        "message": "PMC Officer Query System API is active",
        "docs": "/docs",
        "health": "/api/health",
        "suggest": "/api/query/suggest",
        "execute": "/api/query/execute",
        "reference": "/api/reference/department_master"
    }
