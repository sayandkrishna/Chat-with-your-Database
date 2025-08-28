#!/usr/bin/env python3
"""
Test script to verify the modular architecture works correctly.
This script tests imports and basic functionality of each module.
"""

import sys
import traceback

def test_imports():
    """Test that all modules can be imported successfully."""
    print("🧪 Testing module imports...")
    
    try:
        print("  ✓ Importing config...")
        from config import settings
        print(f"    - Database host: {settings.DB_HOST}")
        print(f"    - Redis host: {settings.REDIS_HOST}")
        
        print("  ✓ Importing models...")
        from models import SemanticCacheEntry, IntentPattern, QueryRequest
        print("    - All Pydantic models imported successfully")
        
        print("  ✓ Importing database...")
        from database import get_db_connection, setup_database_tables
        print("    - Database functions imported successfully")
        
        print("  ✓ Importing cache...")
        from cache import cache_manager
        print("    - Cache manager imported successfully")
        
        print("  ✓ Importing auth...")
        from auth import hash_password, create_access_token
        print("    - Authentication functions imported successfully")
        
        print("  ✓ Importing services...")
        from services import IntentDetectionService, QueryProcessingService, query_orchestrator
        print("    - Service classes imported successfully")
        
        print("  ✓ Importing API...")
        from api import app
        print("    - FastAPI app imported successfully")
        
        print("  ✓ Importing main...")
        from main import app as main_app
        print("    - Main entry point imported successfully")
        
        print("\n✅ All modules imported successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration settings."""
    print("\n🔧 Testing configuration...")
    
    try:
        from config import settings
        
        # Test database config
        db_config = settings.database_config
        assert isinstance(db_config, dict)
        assert "host" in db_config
        assert "database" in db_config
        print("  ✓ Database configuration valid")
        
        # Test Redis config
        assert hasattr(settings, 'REDIS_HOST')
        assert hasattr(settings, 'REDIS_PORT')
        print("  ✓ Redis configuration valid")
        
        # Test JWT config
        assert hasattr(settings, 'JWT_SECRET_KEY')
        assert hasattr(settings, 'JWT_ALGORITHM')
        print("  ✓ JWT configuration valid")
        
        print("✅ Configuration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_models():
    """Test Pydantic models."""
    print("\n📋 Testing data models...")
    
    try:
        from models import QueryRequest, IntentPattern
        
        # Test QueryRequest
        query_data = {"user_query": "test query", "conversation_history": []}
        query_request = QueryRequest(**query_data)
        assert query_request.user_query == "test query"
        print("  ✓ QueryRequest model works")
        
        # Test IntentPattern
        pattern_data = {
            "pattern": r"test",
            "table_hint": "test_table",
            "sql_template": "SELECT * FROM {table}",
            "confidence_score": 0.9
        }
        intent_pattern = IntentPattern(**pattern_data)
        assert intent_pattern.confidence_score == 0.9
        print("  ✓ IntentPattern model works")
        
        print("✅ Models test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Models test failed: {e}")
        return False

def test_services():
    """Test service classes."""
    print("\n⚙️ Testing services...")
    
    try:
        from services import IntentDetectionService, QueryProcessingService
        
        # Test IntentDetectionService
        patterns = IntentDetectionService.INTENT_PATTERNS
        assert len(patterns) > 0
        assert all(hasattr(p, 'pattern') for p in patterns)
        print("  ✓ IntentDetectionService patterns loaded")
        
        # Test QueryProcessingService
        assert hasattr(QueryProcessingService, 'execute_sql_query')
        assert hasattr(QueryProcessingService, 'process_list_tables_request')
        print("  ✓ QueryProcessingService methods available")
        
        print("✅ Services test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Services test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Modular Architecture")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_models,
        test_services
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The modular architecture is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
