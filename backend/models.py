from pydantic import BaseModel
from typing import List, Dict, Optional, Any

class SemanticCacheEntry(BaseModel):
    """Model for semantic cache entries."""
    query: str
    embedding: List[float]
    response: Dict[str, Any]
    timestamp: float
    user_id: str
    hit_count: int = 1

class IntentPattern(BaseModel):
    """Model for intent detection patterns."""
    pattern: str
    table_hint: str
    sql_template: str
    confidence_score: float

class SignupRequest(BaseModel):
    """Model for user signup requests."""
    username: str
    password: str

class LoginRequest(BaseModel):
    """Model for user login requests."""
    username: str
    password: str

class DbConfigRequest(BaseModel):
    """Model for database configuration requests."""
    db_name: str
    db_host: str
    db_database: str
    db_user: str
    db_password: str
    db_port: int

class QueryRequest(BaseModel):
    """Model for LLM query requests."""
    user_query: str
    conversation_id: Optional[int] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None
