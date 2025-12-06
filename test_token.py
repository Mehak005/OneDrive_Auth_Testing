# test_token.py
from msal import PublicClientApplication
import config

print("Testing OneDrive API Access...\n")

# Create the MSAL app
# FIX: Use config.AUTHORITY_URL instead of building the URL manually
app = PublicClientApplication(
    config.CLIENT_ID,
    authority=config.AUTHORITY_URL
)

# Get token interactively (will open browser)
scopes = ["Files.ReadWrite.All", "Sites.ReadWrite.All", "User.Read"]

print("Opening browser for authentication...")
result = app.acquire_token_interactive(scopes=scopes)

if "access_token" in result:
    print("\nSUCCESS! Got access token!")
    print(f"Token (first 50 chars): {result['access_token'][:50]}...")

    # Save token for later use
    with open('token.txt', 'w') as f:
        f.write(result['access_token'])
    print("Token saved to token.txt")
    print("\nYou're ready to test OneDrive API!")
else:
    print("\nERROR getting token:")
    print(f"Error: {result.get('error')}")
    print(f"Description: {result.get('error_description')}")