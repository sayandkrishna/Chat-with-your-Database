

# Smart Database Query API 🤖

**Transform natural language into powerful database queries. This production-ready API uses intent detection, semantic caching, and LLM-powered SQL generation to bridge the gap between human language and your data.**

This API is designed for developers, data analysts, and business users who need to interact with databases without writing complex SQL.

-----

## 🌟 Core Features

  * **Natural Language Processing**:

      * **Intent Detection**: Employs pattern-based recognition for common query types like listing, counting, and filtering.
      * **LLM Integration**: Seamlessly falls back to a language model for complex or ambiguous queries.
      * **Query Understanding**: Performs semantic analysis of user intent and conversation history for contextual understanding.

  * **Performance Optimization**:

      * **Semantic Caching**: Utilizes a Redis-based cache with sentence transformers to store and retrieve results for similar queries, drastically reducing response times.
      * **Intelligent Fallbacks**: Prioritizes fast pattern matching before making more expensive LLM calls.

  * **Database Management**:

      * **Multi-Database Support**: Connect to and manage multiple PostgreSQL databases simultaneously.
      * **Schema Exploration**: Automatically discovers tables, columns, and data types.
      * **Credential Management**: Securely stores and manages database connection credentials.

  * **Security & Authentication**:

      * **JWT Authentication**: Secures endpoints with token-based user authentication.
      * **User Isolation**: Ensures that each user's queries, database configurations, and cache are kept separate.
      * **Password Security**: Uses SHA-256 hashing to protect stored user credentials.

## 🏗️ Technical Architecture

The application is built with a clean, modular design that separates concerns for maintainability and scalability.

```
/
├── api.py             # FastAPI application, route definitions, and endpoint logic
├── auth.py            # JWT authentication, user creation, and password management
├── cache.py           # Redis caching, embedding generation, and semantic similarity logic
├── config.py          # Environment configuration using Pydantic settings
├── database.py        # Database connection management and schema discovery
├── main.py            # Main application entry point
├── models.py          # Pydantic data models for request/response validation
├── services.py        # Core business logic for query orchestration and intent detection
└── requirements.txt   # Python dependencies
```

### Component Responsibilities

  * **`config.py`**: Manages all environment variables and configuration settings.
  * **`models.py`**: Defines Pydantic models for robust data validation of API requests and responses.
  * **`database.py`**: Handles all interactions with the database, from connection pooling to schema discovery.
  * **`cache.py`**: Manages the Redis connection, sentence transformer model, and all caching logic.
  * **`auth.py`**: Implements JWT token creation/validation and user authentication workflows.
  * **`services.py`**: Contains the core business logic, including the query processing pipeline and intent detection algorithms.
  * **`api.py`**: Defines all REST endpoints, handles request/response cycles, and manages errors.

## ⚙️ How It Works: The Query Pipeline

1.  **Input Validation**: An incoming request is first validated against Pydantic models.
2.  **Semantic Cache Check**: The system generates embeddings for the user query and searches Redis for semantically similar cached queries. If a match with a high similarity score is found, the cached response is returned instantly.
3.  **Intent Detection**: If no cache hit occurs, regex patterns are applied to identify the query's intent (e.g., listing tables, counting records) and confidence score.
4.  **Query Execution**: If the intent is recognized with high confidence, a pre-defined SQL template is used to generate and execute a query. If not, the query is passed to an LLM for SQL generation.
5.  **Response Caching**: The final result is stored in the semantic cache with its corresponding embedding for future use.

## 🛠️ Installation & Setup

### Prerequisites

  * Python 3.8+
  * PostgreSQL
  * Redis (for caching)

### Environment Configuration

Create a `.env` file in the project root and add the following variables:

```env
# Database Configuration (for the application's own data)
DB_HOST=localhost
DB_DATABASE=your_db_name
DB_USER=your_username
DB_PASSWORD=your_password
DB_PORT=5432

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
CACHE_EXPIRATION_SECONDS=3600

# JWT Configuration
JWT_SECRET_KEY=a-very-strong-and-secret-key

# Semantic Search Configuration
SEMANTIC_SIMILARITY_THRESHOLD=0.88
INTENT_CONFIDENCE_THRESHOLD=0.8
```

