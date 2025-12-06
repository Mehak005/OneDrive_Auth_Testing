# multi_user_auth.py
"""
Get tokens for multiple users
This allows testing with different user types (owner, collaborator, external)
"""
from msal import PublicClientApplication
import config
import json


def get_token_for_user(user_type):
    """
    Get access token for a specific user

    Args:
        user_type: 'owner' or 'collaborator'

    Returns:
        Access token string or None
    """
    print(f"\n=== Getting token for {user_type.upper()} ===")

    app = PublicClientApplication(
        config.CLIENT_ID,
        authority=config.AUTHORITY_URL
    )

    scopes = ["Files.ReadWrite.All", "Sites.ReadWrite.All", "User.Read"]

    print(f"Opening browser for {user_type} to sign in...")
    print(f"Please sign in with the appropriate account.")

    result = app.acquire_token_interactive(scopes=scopes)

    if "access_token" in result:
        # Save token with user type prefix
        filename = f'token_{user_type}.txt'
        with open(filename, 'w') as f:
            f.write(result['access_token'])

        # Also save user info for reference
        user_info = {
            'user_type': user_type,
            'username': result.get('account', {}).get('username', 'Unknown'),
            'name': result.get('account', {}).get('name', 'Unknown')
        }
        with open(f'user_{user_type}.json', 'w') as f:
            json.dump(user_info, f, indent=2)

        print(f"SUCCESS! Token saved to {filename}")
        print(f"Account: {user_info['username']}")
        return result['access_token']
    else:
        print(f"ERROR: {result.get('error')}")
        print(f"Description: {result.get('error_description')}")
        return None


if __name__ == "__main__":
    print("=" * 70)
    print("MULTI-USER AUTHENTICATION SETUP")
    print("=" * 70)

    print("\nThis script will help you get tokens for multiple users.")
    print("\nYou need to sign in TWICE:")
    print("  1. As OWNER (person who creates and owns files)")
    print("  2. As COLLABORATOR (person testing access to owner's files)")
    print("\nEach sign-in will open a browser window.")
    print("\nIMPORTANT: Use DIFFERENT accounts for each role!")
    print("  - Owner: Your account (mehak.seth2023@gmail.com)")
    print("  - Collaborator: Your teammate's account (srinivasmekala1227@gmail.com)")

    input("\nPress Enter to start...")

    # Get owner token
    print("\n" + "=" * 70)
    print("STEP 1: Get OWNER token")
    print("=" * 70)
    print("Sign in with the OWNER account (person who creates files)")

    owner_token = get_token_for_user('owner')

    if not owner_token:
        print("\nFailed to get owner token. Exiting.")
        exit(1)

    input("\nPress Enter to sign in as COLLABORATOR...")

    # Get collaborator token
    print("\n" + "=" * 70)
    print("STEP 2: Get COLLABORATOR token")
    print("=" * 70)
    print("Sign in with a DIFFERENT account (the collaborator)")
    print("This should be your teammate's account or a second test account.")

    collab_token = get_token_for_user('collaborator')

    if not collab_token:
        print("\nFailed to get collaborator token. Exiting.")
        exit(1)

    # Success
    print("\n" + "=" * 70)
    print("SUCCESS! BOTH TOKENS OBTAINED")
    print("=" * 70)
    print("\nTokens saved:")
    print("  - token_owner.txt")
    print("  - token_collaborator.txt")
    print("\nUser info saved:")
    print("  - user_owner.json")
    print("  - user_collaborator.json")
    print("\nYou can now run the multi-user test framework:")
    print("  python test_framework_multiuser.py")
    print("=" * 70)