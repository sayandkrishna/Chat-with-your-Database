import requests
import json
import time
import re
import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise EnvironmentError("OPENROUTER_API_KEY not found in .env file. Please add it.")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_MODEL = "openai/gpt-oss-20b:free"  # Free model

def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0,
    max_tokens: int = 800,
    retries: int = 3,
    timeout: int = 60,
) -> Dict[str, Any]:
    """Call the OpenRouter API with prompts and parameters."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    for i in range(retries):
        try:
            print(f"Calling OpenRouter API (Attempt {i + 1}/{retries})...")
            response = requests.post(
                OPENROUTER_URL, headers=headers, json=data, timeout=timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"HTTP error on attempt {i + 1}: {e}")
            if i < retries - 1:
                time.sleep(2**i)
            else:
                raise ConnectionError(f"Failed to connect to OpenRouter after {retries} retries.") from e
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise


def extract_table_info_from_schemas(all_db_schemas: Dict) -> str:
    """Create a more concise schema representation focusing on key information."""
    schema_lines = []
    
    for db_name, tables in all_db_schemas.items():
        if not tables:
            continue
            
        schema_lines.append(f"DATABASE '{db_name}':")
        
        for table_name, columns in tables.items():
            # Get primary columns and data types
            key_columns = []
            all_columns = []
            
            for col in columns:
                col_name = col.get("column_name", "")
                data_type = col.get("data_type", "")
                if col_name and data_type:
                    col_desc = f"{col_name}({data_type})"
                    all_columns.append(col_desc)
                    
                    # Identify likely key columns
                    if any(keyword in col_name.lower() for keyword in ['id', 'key', 'pk', 'primary']):
                        key_columns.append(col_desc)
            
            # Show table with key columns highlighted
            if key_columns:
                schema_lines.append(f"  • {table_name}: {', '.join(key_columns)} + {len(all_columns) - len(key_columns)} more")
            else:
                # Show first few columns if no clear keys
                shown_cols = all_columns[:3]
                remaining = len(all_columns) - len(shown_cols)
                if remaining > 0:
                    schema_lines.append(f"  • {table_name}: {', '.join(shown_cols)} + {remaining} more")
                else:
                    schema_lines.append(f"  • {table_name}: {', '.join(shown_cols)}")
        
        schema_lines.append("")
    
    return "\n".join(schema_lines)


def build_conversation_context(conversation_history: Optional[List[Dict]] = None) -> tuple[str, str, str]:
    """Extract context from conversation history."""
    if not conversation_history:
        return "No previous conversation.", None, None
    
    context_lines = ["RECENT CONVERSATION:"]
    last_db = last_table = None
    
    # Process last few turns (limit to avoid token overflow)
    recent_turns = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
    
    for turn in recent_turns:
        role = turn.get("role", "")
        content = turn.get("content", "")
        
        if role == "user":
            context_lines.append(f"User: {content}")
        elif role == "assistant":
            if isinstance(content, dict):
                # Extract database and table info
                # Check for both new (inferred) and old key names for compatibility
                db_key = "inferred_db_name" if "inferred_db_name" in content else "db"
                table_key = "inferred_table" if "inferred_table" in content else "table"

                if db_key in content:
                    last_db = content[db_key]
                if table_key in content:
                    last_table = content[table_key]
                
                # Summarize assistant response
                if content.get("action") == "list_tables":
                    db_name = content.get(db_key, 'unknown')
                    context_lines.append(f"Assistant: Listed tables in database '{db_name}'")
                elif "sql_query" in content:
                    table_name = content.get(table_key, 'unknown')
                    context_lines.append(f"Assistant: Executed query on {table_name} table")
                else:
                    context_lines.append(f"Assistant: {json.dumps(content)[:100]}...")
            else:
                context_lines.append(f"Assistant: {str(content)[:100]}...")
    context_str = "\n".join(context_lines)
    return context_str, last_db, last_table


def create_enhanced_prompts(user_query: str, all_db_schemas: Dict, conversation_history: Optional[List[Dict]] = None) -> tuple[str, str]:
    """Create optimized system and user prompts for better LLM performance."""
    
    # Build schema information
    schema_info = extract_table_info_from_schemas(all_db_schemas)
    
    # Build conversation context
    context_str, last_db, last_table = build_conversation_context(conversation_history)
    
    # Enhanced system prompt
    system_prompt = """You are an expert SQL assistant. Your job is to interpret natural language queries and convert them to structured database operations.

RULES:
1. Always output valid JSON only
2. For data queries: {"db": "database_name", "table": "table_name", "query": "SELECT ..."}
3. For listing tables: {"db": "database_name", "action": "list_tables"}
4. If unsure: {}

GUIDELINES:
- Use LIMIT clause for SELECT queries (default 100 rows)
- Prefer exact table name matches
- Use context from previous queries when database/table not specified
- Keep SQL simple and safe (SELECT only, no DROP/DELETE)
- Match user's intent even if they use approximate table names
- For string comparisons in WHERE clauses, use ILIKE for case-insensitive matching (e.g., `WHERE name ILIKE 'iphone%'`)."""

    # Build memory instructions
    memory_hint = ""
    if last_db or last_table:
        memory_hint = f"\nCONTEXT: Previous query used database='{last_db}', table='{last_table}'. Reuse if current query doesn't specify them."
    
    # Enhanced user prompt
    user_prompt = f"""DATABASE SCHEMA:
{schema_info}

{context_str}
{memory_hint}

USER QUERY: "{user_query}"

Think step by step:
1. What is the user asking for?
2. Which database and table are relevant?
3. What SQL query or action is needed?

JSON OUTPUT:"""

    return system_prompt, user_prompt


def validate_and_clean_response(raw_response: str) -> Dict[str, Any]:
    """Extract and validate JSON from LLM response."""
    try:
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if not json_match:
            print(f"No JSON found in response: {raw_response}")
            return {}
        
        # Parse JSON
        parsed = json.loads(json_match.group(0))
        
        # Validate structure
        if not parsed:
            return {}
        
        # Validate list_tables action
        if parsed.get("action") == "list_tables":
            if "db" not in parsed:
                print("Missing 'db' key for list_tables action")
                return {}
            return parsed
        
        # Validate query action
        if "query" in parsed:
            required_keys = ["db", "table", "query"]
            missing_keys = [key for key in required_keys if key not in parsed]
            if missing_keys:
                print(f"Missing keys for query: {missing_keys}")
                return {}
            
            # Basic SQL safety check
            query = parsed["query"].upper()
            dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
            if any(keyword in query for keyword in dangerous_keywords):
                print(f"Potentially dangerous SQL detected: {parsed['query']}")
                return {}
            
            return parsed
        
        # If we get here, the structure is unclear
        print(f"Unclear response structure: {parsed}")
        return {}
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return {}
    except Exception as e:
        print(f"Error validating response: {e}")
        return {}


def llmcall(user_query: str, all_db_schemas: Dict, conversation_history: Optional[List[Dict]] = None) -> str:
    """
    Enhanced LLM call with better prompting and validation.
    
    Args:
        user_query: Natural language query from user
        all_db_schemas: Complete database schema information
        conversation_history: Previous conversation for context
    
    Returns:
        JSON string with database operation or empty dict on failure
    """
    
    try:
        # Create optimized prompts
        system_prompt, user_prompt = create_enhanced_prompts(
            user_query, all_db_schemas, conversation_history
        )
        
        # Debug: Print prompts (remove in production)
        print("=" * 50)
        print("SYSTEM PROMPT:")
        print(system_prompt[:300] + "..." if len(system_prompt) > 300 else system_prompt)
        print("\nUSER PROMPT:")
        print(user_prompt[:500] + "..." if len(user_prompt) > 500 else user_prompt)
        print("=" * 50)
        
        # Call LLM with optimized settings
        raw_response = call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,  # Slightly higher for creativity
            max_tokens=1024,   # Reduce tokens for faster response
            retries=2,        # Fewer retries for speed
            timeout=30        # Shorter timeout
        )
        
        # Extract text response
        text_output = raw_response["choices"][0]["message"]["content"].strip()
        print(f"Raw LLM Response: {text_output}")
        
        # Validate and clean response
        parsed_output = validate_and_clean_response(text_output)
        
        if parsed_output:
            print(f"✅ Valid LLM Output: {parsed_output}")
        else:
            print("❌ LLM returned invalid or empty response")
        
        return json.dumps(parsed_output)
        
    except ConnectionError as e:
        print(f"Connection error: {e}")
        return "{}"
    except Exception as e:
        print(f"Unexpected error in llmcall: {e}")
        return "{}"


# --- Additional Helper Functions ---




# if __name__ == "__main__":
#     # Run tests if script is executed directly
#     test_llm_with_sample_queries()