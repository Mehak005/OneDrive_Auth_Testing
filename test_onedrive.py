import requests
import msal
import sys
import config  # Importing your separate config file


def get_valid_token():
    """
    Authenticates using the settings in config.py.
    """
    # Create the app instance using the 'common' authority from config
    app = msal.PublicClientApplication(
        config.CLIENT_ID,
        authority=config.AUTHORITY_URL
    )

    # 1. Check if a token is already cached in memory
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(config.SCOPES, account=accounts[0])

    # 2. If no token, log in interactively (browser popup)
    if not result:
        print("No cached token found. Please sign in via the browser...")
        result = app.acquire_token_interactive(scopes=config.SCOPES)

    if "access_token" in result:
        return result["access_token"]
    else:
        print(f"Authentication Failed: {result.get('error')}")
        print(f"Description: {result.get('error_description')}")
        sys.exit(1)


# ==========================================
# MAIN TEST EXECUTION
# ==========================================
if __name__ == "__main__":
    # Get a fresh token using the config settings
    token = get_valid_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # --- Test 1: User Info ---
    print("\n=== TEST 1: Get User Info ===")
    response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
    if response.status_code == 200:
        user = response.json()
        print(f"SUCCESS - Signed in as: {user.get('userPrincipalName', user.get('mail'))}")
    else:
        print(f"ERROR: {response.text}")

    # --- Test 2: Drive Info ---
    print("\n=== TEST 2: Get Drive Info ===")
    response = requests.get("https://graph.microsoft.com/v1.0/me/drive", headers=headers)
    if response.status_code == 200:
        drive = response.json()
        print(f"SUCCESS - Drive ID: {drive['id']}")
        print(f"Drive Type: {drive.get('driveType', 'Unknown')}")
    else:
        print(f"ERROR: {response.text}")

    # --- Test 3: List Files ---
    print("\n=== TEST 3: List Root Folder ===")
    response = requests.get("https://graph.microsoft.com/v1.0/me/drive/root/children", headers=headers)
    if response.status_code == 200:
        items = response.json()
        print(f"SUCCESS - Found {len(items.get('value', []))} items")
    else:
        print(f"ERROR: {response.text}")

    # --- Test 4: Upload File ---
    print("\n=== TEST 4: Create Test File ===")
    response = requests.put(
        "https://graph.microsoft.com/v1.0/me/drive/root:/test_auth_file.txt:/content",
        headers=headers,
        data=b"This is a test file for authorization testing"
    )
    if response.status_code in [200, 201]:
        print(f"SUCCESS - Created file: {response.json()['name']}")
    else:
        print(f"ERROR: {response.text}")