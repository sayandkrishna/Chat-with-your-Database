"""
Main entry point for the Database Query API.

This application provides a smart database query interface with:
- Semantic caching using Redis and sentence transformers
- Intent detection for natural language queries
- JWT-based authentication
- Multi-database support
- LLM fallback for complex queries
"""

from api import app

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Database Query API...")
    print("📚 Features: Semantic Caching, Intent Detection, Multi-DB Support")
    print("🔐 Authentication: JWT-based")
    print("💾 Cache: Redis with semantic similarity")
    print("🤖 AI: Intent detection + LLM fallback")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
