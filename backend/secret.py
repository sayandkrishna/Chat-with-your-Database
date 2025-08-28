import secrets

# Generate a URL-safe, random text string of 32 characters
secret_key = secrets.token_urlsafe(32) 
print(secret_key)