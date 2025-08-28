from fastapi import FastAPI, HTTPException, status, Depends
from typing import List, Dict, Any
import time
import psycopg2
# In api.py

from fastapi.middleware.cors import CORSMiddleware

# Add this right after app = FastAPI(...)

from models import (
    SignupRequest, LoginRequest, DbConfigRequest, QueryRequest
)
from auth import (
    get_current_user_id, authenticate_user, create_user, create_access_token
)
from database import (
    get_db_connection, get_user_db_credentials, get_all_table_names
)
from services import query_orchestrator
from cache import cache_manager
from config import settings

# Create the FastAPI app instance
app = FastAPI(
    title="Database Query API",
    description="A smart database query API with semantic caching and intent detection",
    version="1.0.0"
)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # The address of your React app
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    try:
        from database import setup_database_tables
        setup_database_tables()
        print("Application startup completed successfully")
    except Exception as e:
        print(f"Startup error: {e}")
        raise

# --- Authentication Endpoints ---
@app.post("/signup", tags=["Authentication"])
async def signup(request: SignupRequest):
    """Create a new user account."""
    user_id = create_user(request.username, request.password)
    if user_id:
        return {"message": "User created successfully", "user_id": user_id}
    else:
        raise HTTPException(status_code=400, detail="Username already exists")

@app.post("/login", tags=["Authentication"])
async def login(request: LoginRequest):
    """Authenticate a user and return a JWT token."""
    user_id = authenticate_user(request.username, request.password)
    if user_id:
        access_token = create_access_token(data={"user_id": user_id})
        return {
            "message": "Login successful",
            "user_id": user_id,
            "username": request.username,
            "access_token": access_token,
            "token_type": "bearer"
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

# --- Database Management Endpoints ---
@app.post("/save-db-config", tags=["Database Management"])
async def save_db_config(request: DbConfigRequest, user_id: str = Depends(get_current_user_id)):
    """Save database configuration for a user."""
    conn = None
    try:
        conn = get_db_connection(settings.database_config)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO db_credentials (user_id, db_name, db_host, db_database, db_user, db_password, db_port)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, db_name) DO UPDATE SET
            db_host = EXCLUDED.db_host,
            db_database = EXCLUDED.db_database,
            db_user = EXCLUDED.db_user,
            db_password = EXCLUDED.db_password,
            db_port = EXCLUDED.db_port;
        """, (user_id, request.db_name, request.db_host, request.db_database, request.db_user, request.db_password, request.db_port))
        conn.commit()
        return {"message": "Database credentials saved successfully"}
    except Exception as e:
        print(f"Error saving DB config: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            cur.close()
            conn.close()

@app.get("/list-dbs", tags=["Database Management"])
async def list_user_databases(user_id: str = Depends(get_current_user_id)):
    """List all database configurations for a user."""
    conn = None
    try:
        conn = get_db_connection(settings.database_config)
        cur = conn.cursor()
        databases = []
        cur.execute("SELECT db_name, db_host, db_database, db_user, db_port FROM db_credentials WHERE user_id = %s", (user_id,))
        for row in cur.fetchall():
            databases.append({
                "db_name": row[0],
                "config": {
                    "host": row[1],
                    "database": row[2],
                    "user": row[3],
                    "port": row[4]
                }
            })
        return {"databases": databases}
    except Exception as e:
        print(f"Error listing databases for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            cur.close()
            conn.close()

@app.get("/list-tables/{db_name}", tags=["Database Management"])
async def list_db_tables(db_name: str, user_id: str = Depends(get_current_user_id)):
    """List all tables in a specific database."""
    creds_conn = None
    try:
        creds_conn = get_db_connection(settings.database_config)
        creds_cur = creds_conn.cursor()
        db_config = get_user_db_credentials(creds_cur, user_id, db_name)
        
        if not db_config:
            raise HTTPException(status_code=404, detail=f"Database configuration '{db_name}' not found or you do not have access.")
            
        table_names = get_all_table_names(db_config)
        return {"tables": table_names}
    except Exception as e:
        print(f"Error listing tables for db {db_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if creds_conn:
            creds_cur.close()
            creds_conn.close()

# --- Enhanced Ask Endpoint with Semantic Caching ---
@app.post("/ask", tags=["LLM Interaction"])
async def ask_llm(request: QueryRequest, user_id: str = Depends(get_current_user_id)):
    """Enhanced query handler with semantic caching and intent detection."""
    try:
        return query_orchestrator.process_query(
            user_id, 
            request.user_query.strip(), 
            request.conversation_history
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# --- Cache Management Endpoints ---
@app.get("/cache-stats", tags=["Cache Management"])
async def get_cache_stats(user_id: str = Depends(get_current_user_id)):
    """Get semantic cache statistics for the current user."""
    return cache_manager.get_cache_stats(user_id)

@app.delete("/clear-cache", tags=["Cache Management"])
async def clear_user_cache(user_id: str = Depends(get_current_user_id)):
    """Clear all cached queries for the current user."""
    return cache_manager.clear_user_cache(user_id)

# --- Debug Endpoints ---
@app.post("/debug-intent", tags=["Debug"])
async def debug_intent_detection(request: QueryRequest, user_id: str = Depends(get_current_user_id)):
    """Debug endpoint to test intent detection without executing queries."""
    from database import get_all_user_db_schemas
    from services import IntentDetectionService
    
    all_user_schemas = get_all_user_db_schemas(user_id)
    if not all_user_schemas:
        raise HTTPException(status_code=404, detail="No database connections found.")
    
    intent_result = IntentDetectionService.detect_intent(request.user_query, all_user_schemas)
    
    return {
        "query": request.user_query,
        "intent_detected": intent_result is not None,
        "intent_result": intent_result,
        "available_patterns": [
            {
                "pattern": p.pattern,
                "confidence": p.confidence_score,
                "sql_template": p.sql_template
            }
            for p in IntentDetectionService.INTENT_PATTERNS
        ]
    }

@app.post("/debug-embedding", tags=["Debug"])
async def debug_embedding_similarity(query1: str, query2: str):
    """Debug endpoint to test semantic similarity between two queries."""
    if not cache_manager.embedding_model:
        raise HTTPException(status_code=503, detail="Embedding model not available")
    
    try:
        embedding1 = cache_manager.get_query_embedding(query1)
        embedding2 = cache_manager.get_query_embedding(query2)
        
        if embedding1 is None or embedding2 is None:
            raise HTTPException(status_code=500, detail="Failed to generate embeddings")
        
        from sklearn.metrics.pairwise import cosine_similarity
        similarity = cosine_similarity(
            embedding1.reshape(1, -1), 
            embedding2.reshape(1, -1)
        )[0][0]
        
        return {
            "query1": query1,
            "query2": query2,
            "similarity": float(similarity),
            "would_cache_hit": similarity > settings.SEMANTIC_SIMILARITY_THRESHOLD,
            "threshold": settings.SEMANTIC_SIMILARITY_THRESHOLD
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating similarity: {e}")

# --- Health Check ---
@app.get("/health", tags=["System"])
async def health_check():
    """System health check including cache and embedding model status."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "database": "unknown",
            "redis_cache": "unknown",
            "embedding_model": "unknown"
        }
    }
    
    # Check database
    try:
        conn = get_db_connection(settings.database_config)
        conn.close()
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {e}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        if cache_manager.client:
            cache_manager.client.ping()
            health_status["components"]["redis_cache"] = "healthy"
        else:
            health_status["components"]["redis_cache"] = "disabled"
    except Exception as e:
        health_status["components"]["redis_cache"] = f"unhealthy: {e}"
        health_status["status"] = "degraded"
    
    # Check embedding model
    try:
        if cache_manager.embedding_model:
            # Quick test embedding
            test_embedding = cache_manager.get_query_embedding("test query")
            if test_embedding is not None:
                health_status["components"]["embedding_model"] = "healthy"
            else:
                health_status["components"]["embedding_model"] = "unhealthy: failed to generate embedding"
                health_status["status"] = "degraded"
        else:
            health_status["components"]["embedding_model"] = "disabled"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["embedding_model"] = f"unhealthy: {e}"
        health_status["status"] = "degraded"
    
    return health_status