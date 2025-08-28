import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application configuration settings."""
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    CACHE_EXPIRATION_SECONDS: int = int(os.getenv("CACHE_EXPIRATION_SECONDS", 3600))
    
    # Semantic Search Configuration
    SEMANTIC_SIMILARITY_THRESHOLD: float = float(os.getenv("SEMANTIC_SIMILARITY_THRESHOLD", 0.88))
    INTENT_CONFIDENCE_THRESHOLD: float = float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", 0.8))
    
    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_DATABASE: str = os.getenv("DB_DATABASE", "mydb")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "root")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-that-you-should-change")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    @property
    def database_config(self) -> dict:
        """Get database configuration dictionary."""
        return {
            "host": self.DB_HOST,
            "database": self.DB_DATABASE,
            "user": self.DB_USER,
            "password": self.DB_PASSWORD,
            "port": self.DB_PORT
        }

# Global settings instance
settings = Settings()
