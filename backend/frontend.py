import streamlit as st
import requests
import pandas as pd
import json

# --- Configuration ---
# Make sure your FastAPI backend is running at this address
API_URL = "http://127.0.0.1:8000"

# --- Page & Session State Setup ---
st.set_page_config(page_title="DB Chat AI", layout="wide", initial_sidebar_state="expanded")

# Initialize session state variables to persist data across reruns
def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state: 
        st.session_state.username = None   
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "databases" not in st.session_state:
        st.session_state.databases = []
    if "messages" not in st.session_state:
        st.session_state.messages = []

init_session_state()

# --- API Helper Functions ---
def login_user(username, password):
    try:
        response = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
        if response.status_code == 200:
            return response.json()
        st.error(f"Login Failed: {response.json().get('detail', 'Unknown error')}")
        return None
    except requests.ConnectionError:
        st.error("Connection Error: Could not connect to the backend. Is it running?")
        return None

def signup_user(username, password):
    try:
        response = requests.post(f"{API_URL}/signup", json={"username": username, "password": password})
        if response.status_code == 200:
            st.success("Signup successful! Please log in.")
            return True
        st.error(f"Signup Failed: {response.json().get('detail', 'Username may already exist.')}")
        return False
    except requests.ConnectionError:
        st.error("Connection Error: Could not connect to the backend.")
        return False

def get_user_databases(token):
    headers = {"token": token}
    try:
        response = requests.get(f"{API_URL}/list-dbs", headers=headers)
        if response.status_code == 200:
            return response.json().get("databases", [])
        return []
    except requests.ConnectionError:
        st.error("Connection Error: Could not fetch databases.")
        return []

def save_db_config(token, config):
    headers = {"token": token}
    try:
        response = requests.post(f"{API_URL}/save-db-config", headers=headers, json=config)
        if response.status_code == 200:
            st.success("Database configuration saved successfully!")
            return True
        st.error(f"Failed to save: {response.json().get('detail')}")
        return False
    except requests.ConnectionError:
        st.error("Connection Error: Could not save configuration.")
        return False

# In frontend.py

def ask_llm(token, query, history: list = None): # Add history parameter
    headers = {"token": token}
    # Create the payload including the history
    payload = {
        "user_query": query,
        "conversation_history": history or []
    }
    try:
        # Send the payload
        response = requests.post(f"{API_URL}/ask", headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()
        st.error(f"Error from AI: {response.json().get('detail')}")
        return None
    except requests.ConnectionError:
        st.error("Connection Error: Could not connect to the backend.")
        return None
# --- UI Rendering Functions ---

def display_login_page():
    """Shows the centered Login/Sign Up form."""
    st.title("Welcome to Database Chat AI 🤖")
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            login_tab, signup_tab = st.tabs(["**Login**", "**Sign Up**"])

            with login_tab:
                with st.form("login_form"):
                    username_input = st.text_input("Username", key="login_user") # Renamed variable
                    password = st.text_input("Password", type="password", key="login_pass")
                    submitted = st.form_submit_button("Login", use_container_width=True)
                    if submitted:
                        user_data = login_user(username_input, password)
                        if user_data:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_data["user_id"]
                            st.session_state.username = user_data["username"] # <-- ADD THIS LINE
                            st.session_state.access_token = user_data["access_token"]
                            st.rerun()
            with signup_tab:
                with st.form("signup_form"):
                    username = st.text_input("Choose a Username", key="signup_user")
                    password = st.text_input("Choose a Password", type="password", key="signup_pass")
                    submitted = st.form_submit_button("Sign Up", use_container_width=True)
                    if submitted:
                        signup_user(username, password)

# In frontend.py

def display_sidebar():
    """Renders the sidebar with DB list and add new DB form."""
    with st.sidebar:
        st.title("🗂️ Databases")
        # CORRECTED LINE: Display the username, not the user_id
        st.markdown(f"User: **{st.session_state.username}**") 
        
        # Fetch and display databases
        if not st.session_state.databases:
             with st.spinner("Loading databases..."):
                st.session_state.databases = get_user_databases(st.session_state.access_token)

        for db in st.session_state.databases:
            with st.container(border=True):
                st.subheader(f"🔹 {db['db_name']}")
                st.write(f"**Host:** {db['config']['host']}")
                st.write(f"**User:** {db['config']['user']}")

        # Form to add a new database
        with st.expander("🔗 Connect New Database"):
            with st.form("new_db_form", clear_on_submit=True):
                db_name = st.text_input("Connection Name (Alias)")
                # You can add the db_type selector here if you've implemented multi-db support
                # db_type = st.selectbox("Database Type", ["postgres", "mysql"])
                db_host = st.text_input("Host", value="localhost")
                db_database = st.text_input("Database Name")
                db_user = st.text_input("User")
                db_password = st.text_input("Password", type="password")
                db_port = st.number_input("Port", value=5432)
                
                submitted = st.form_submit_button("Save Connection")
                if submitted:
                    config = {
                        "db_name": db_name, "db_host": db_host, "db_database": db_database,
                        "db_user": db_user, "db_password": db_password, "db_port": db_port
                        # "db_type": db_type 
                    }
                    if save_db_config(st.session_state.access_token, config):
                        st.session_state.databases = []
                        st.rerun()

        st.button("Logout", on_click=logout, use_container_width=True)
def display_chat_interface():
    """Renders the main chat area, handles message display, and user input."""
    st.title("Chat with your Data 💬")

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Check for complex content (dict) vs. simple string
            if isinstance(message["content"], dict):
                response_data = message["content"]
                
                # Display a summary message
                summary = f"I found **{response_data.get('rows_returned', 0)}** results from the " \
                          f"`{response_data.get('inferred_table', 'N/A')}` table in the " \
                          f"`{response_data.get('inferred_db_name', 'N/A')}` database."
                
                # Add a cache indicator if the response is from the cache
                if response_data.get("source") == "cache":
                    summary += " ⚡️ *From Cache*"
                
                st.markdown(summary)

                # Display the SQL query in an expander
                with st.expander("Show Generated SQL Query"):
                    st.code(response_data.get('sql_query', 'No SQL query available.'), language="sql")

                # Display the data as a dataframe
                if response_data.get('data'):
                    df = pd.DataFrame(response_data['data'])
                    st.dataframe(df)
            else:
                # For simple string messages (like user prompts or errors)
                st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Ask a question about your data..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Get the last 4 messages for conversational context
                history = st.session_state.messages[-5:-1]
                
                # Pass the history in the API call
                response = ask_llm(st.session_state.access_token, prompt, history)
                
                if response:
                    # Append the full, rich dictionary response
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    # Handle cases where the API call failed
                    error_message = "I couldn't process that request. Please try rephrasing or check the backend logs."
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
            
            # Rerun to display the new assistant message immediately
            st.rerun()
def logout():
    """Clears the session state to log the user out."""
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.access_token = None
    st.session_state.databases = []
    st.session_state.messages = []
    st.rerun()

# --- Main Application Logic ---
if not st.session_state.logged_in:
    display_login_page()
else:
    display_sidebar()
    display_chat_interface()
    