import re
import pandas as pd
import psycopg2
from typing import Dict, List, Optional, Any
from models import IntentPattern
from config import settings
from database import get_db_connection, get_user_db_credentials, get_all_table_names
from cache import cache_manager

class IntentDetectionService:
    """Service for detecting user intent from natural language queries."""
    
    # Intent detection patterns
    INTENT_PATTERNS = [
        IntentPattern(
            pattern=r"^(?:list|show|get|find)\s+(?:all\s+)?([\w_]+)$",
            table_hint=r"\1",
            sql_template="SELECT * FROM {table} LIMIT 100;",
            confidence_score=0.95
        ),
        IntentPattern(
            pattern=r"show\s+(?:all\s+)?(?:records?|rows?|data)\s+from\s+(\w+)",
            table_hint=r"\1",
            sql_template="SELECT * FROM {table} LIMIT 100;",
            confidence_score=0.9
        ),
        IntentPattern(
            pattern=r"count\s+(?:records?|rows?)\s+in\s+(\w+)",
            table_hint=r"\1",
            sql_template="SELECT COUNT(*) as count FROM {table};",
            confidence_score=0.9
        ),
        IntentPattern(
            pattern=r"list\s+(?:all\s+)?(?:tables?|schemas?)",
            table_hint="",
            sql_template="LIST_TABLES",
            confidence_score=0.95
        ),
        IntentPattern(
            pattern=r"(?:find|search|get)\s+(\w+)\s+where\s+(\w+)\s*=\s*['\"]?([^'\"]+)['\"]?",
            table_hint=r"\1",
            sql_template="SELECT * FROM {table} WHERE {column} ILIKE '{value}' LIMIT 50;",
            confidence_score=0.8
        ),
        IntentPattern(
            pattern=r"(?:top|first)\s+(\d+)\s+(?:records?|rows?)\s+from\s+(\w+)",
            table_hint=r"\2",
            sql_template="SELECT * FROM {table} LIMIT {limit};",
            confidence_score=0.85
        )
    ]
    
    @classmethod
    def detect_intent(cls, query: str, all_schemas: Dict) -> Optional[Dict[str, Any]]:
        """Detect user intent using pattern matching."""
        query_lower = query.lower().strip()
        
        # Get all available tables for context
        all_tables = []
        for db_name, tables in all_schemas.items():
            all_tables.extend([(db_name, table_name, columns) for table_name, columns in tables.items()])
        
        for pattern in cls.INTENT_PATTERNS:
            match = re.search(pattern.pattern, query_lower, re.IGNORECASE)
            if match:
                print(f"🔍 Pattern matched: {pattern.pattern}")
                
                # Special case for list tables
                if pattern.sql_template == "LIST_TABLES":
                    # Try to infer which database they want
                    db_name = None
                    for db in all_schemas.keys():
                        if db.lower() in query_lower:
                            db_name = db
                            break
                    if not db_name and all_schemas:
                        db_name = list(all_schemas.keys())[0]  # Default to first DB
                    
                    return {
                        "action": "list_tables",
                        "db": db_name,
                        "confidence": pattern.confidence_score,
                        "source": "intent_detection"
                    }
                
                # For SQL queries, try to match table names
                table_hint = pattern.table_hint
                if table_hint and match.groups():
                    # Replace regex groups in table hint
                    for i, group in enumerate(match.groups(), 1):
                        table_hint = table_hint.replace(f"\\{i}", group)
                
                # Find matching table
                matched_table = None
                matched_db = None
                for db_name, table_name, columns in all_tables:
                    if table_hint.lower() in table_name.lower() or table_name.lower() in table_hint.lower():
                        matched_table = table_name
                        matched_db = db_name
                        break
                
                if matched_table and matched_db:
                    # Build SQL from template
                    sql_query = pattern.sql_template.format(
                        table=matched_table,
                        column=match.group(2) if len(match.groups()) >= 2 else "id",
                        value=match.group(3) if len(match.groups()) >= 3 else "",
                        limit=match.group(1) if pattern.pattern.startswith(r"(?:top|first)") else "100"
                    )
                    
                    return {
                        "db": matched_db,
                        "table": matched_table,
                        "query": sql_query,
                        "confidence": pattern.confidence_score,
                        "source": "intent_detection"
                    }
        
        return None

class QueryProcessingService:
    """Service for processing and executing database queries."""
    
    @staticmethod
    def execute_sql_query(db_config: Dict, sql_query: str) -> Dict[str, Any]:
        """Execute a SQL query and return the results."""
        conn = None
        try:
            conn = get_db_connection(db_config)
            df = pd.read_sql(sql_query, conn)
            return {
                "rows_returned": len(df),
                "data": df.to_dict(orient="records")
            }
        except Exception as e:
            raise Exception(f"Error executing SQL query: {e}")
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def process_list_tables_request(user_id: str, db_name: str) -> Dict[str, Any]:
        """Process a request to list tables for a specific database."""
        creds_conn = None
        try:
            creds_conn = get_db_connection(settings.database_config)
            creds_cur = creds_conn.cursor()
            db_config = get_user_db_credentials(creds_cur, user_id, db_name)
            
            if not db_config:
                raise Exception(f"Database '{db_name}' not found or you lack access.")
            
            table_names = get_all_table_names(db_config)
            return {
                "inferred_db_name": db_name,
                "action": "list_tables",
                "data": table_names
            }
        finally:
            if creds_conn:
                creds_conn.close()
    
    @staticmethod
    def process_sql_query_request(user_id: str, inferred_db_name: str, inferred_table: str, sql_query: str) -> Dict[str, Any]:
        """Process a SQL query request."""
        # Get database credentials
        creds_conn = None
        try:
            creds_conn = get_db_connection(settings.database_config)
            current_db_config = get_user_db_credentials(creds_conn.cursor(), user_id, inferred_db_name)
        finally:
            if creds_conn:
                creds_conn.close()
        
        if not current_db_config:
            raise Exception(f"Database configuration '{inferred_db_name}' not found.")
        
        # Execute the query
        query_result = QueryProcessingService.execute_sql_query(current_db_config, sql_query)
        
        return {
            "inferred_db_name": inferred_db_name,
            "inferred_table": inferred_table,
            "sql_query": sql_query,
            **query_result
        }

class LLMService:
    """Service for interacting with the LLM."""
    
    @staticmethod
    def process_with_llm(user_query: str, all_user_schemas: Dict, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Process a query using the LLM."""
        try:
            from test import llmcall
            import json
            
            llm_response_str = llmcall(
                user_query,
                all_user_schemas,
                conversation_history
            )
            return json.loads(llm_response_str)
        except Exception as e:
            raise Exception(f"Error calling LLM or parsing its response: {e}")

class QueryOrchestrator:
    """Main orchestrator for processing user queries."""
    
    def __init__(self):
        self.intent_service = IntentDetectionService()
        self.query_service = QueryProcessingService()
        self.llm_service = LLMService()
    
    def process_query(self, user_id: str, user_query: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Main method to process a user query through the entire pipeline."""
        print(f"🔍 Processing query: {user_query}")
        
        # Step 1: Get user's database schemas
        from database import get_all_user_db_schemas
        all_user_schemas = get_all_user_db_schemas(user_id)
        if not all_user_schemas:
            raise Exception("No database connections found. Please add a database configuration first.")
        
        # Step 2: Generate embedding for semantic similarity
        query_embedding = cache_manager.get_query_embedding(user_query)
        
        # Step 3: Check semantic cache first
        if query_embedding is not None:
            similar_match = cache_manager.find_similar_cached_query(user_id, user_query, query_embedding)
            if similar_match:
                response = similar_match["response"].copy()
                response["source"] = "semantic_cache"
                response["similarity_score"] = similar_match["similarity"]
                response["original_cached_query"] = similar_match["original_query"]
                print(f"✅ Returning semantic cache hit")
                return response
        
        # Step 4: Try intent detection with patterns
        intent_result = self.intent_service.detect_intent(user_query, all_user_schemas)
        if intent_result and intent_result.get("confidence", 0) > settings.INTENT_CONFIDENCE_THRESHOLD:
            print(f"🎯 Intent detection successful (confidence: {intent_result['confidence']})")
            
            try:
                if intent_result.get("action") == "list_tables":
                    final_response = self.query_service.process_list_tables_request(
                        user_id, intent_result.get("db")
                    )
                elif "query" in intent_result:
                    final_response = self.query_service.process_sql_query_request(
                        user_id,
                        intent_result.get("db"),
                        intent_result.get("table"),
                        intent_result.get("query")
                    )
                else:
                    raise Exception("Unknown intent action")
                
                final_response["source"] = "intent_detection"
                final_response["confidence"] = intent_result["confidence"]
                
                # Cache this result
                if query_embedding is not None:
                    cache_manager.store_semantic_cache(user_id, user_query, query_embedding, final_response)
                
                return final_response
                
            except Exception as e:
                print(f"Error executing intent-detected query: {e}")
                # Fall through to OSS LLM on execution error
        
        # Step 5: Fallback to OSS LLM
        print(f"🔄 Escalating to OSS LLM (no cache hit or intent detection failed)")
        try:
            llm_output = self.llm_service.process_with_llm(user_query, all_user_schemas, conversation_history)
        except Exception as e:
            raise Exception(f"An error occurred during LLM processing: {e}")
        
        # Process LLM response
        try:
            if llm_output.get("action") == "list_tables":
                final_response = self.query_service.process_list_tables_request(
                    user_id, llm_output.get("db")
                )
            elif "query" in llm_output:
                final_response = self.query_service.process_sql_query_request(
                    user_id,
                    llm_output.get("db"),
                    llm_output.get("table"),
                    llm_output.get("query")
                )
            else:
                raise Exception(f"LLM returned an unrecognized response format: {llm_output}")
            
            final_response["source"] = "llm_fallback"
            
            # Cache this LLM result
            if query_embedding is not None:
                cache_manager.store_semantic_cache(user_id, user_query, query_embedding, final_response)
            
            return final_response
            
        except Exception as e:
            raise Exception(f"Error processing LLM response: {e}")

# Global service instances
query_orchestrator = QueryOrchestrator()
