# test_token.py
import sys
from msal import PublicClientApplication
import config

def main():
    """
    Acquire an access token interactively and save it to a specified file.
    Usage: python test_token.py <output_filename>
    """
    print("\nChoose the user to generate a token for:")
    print("1. Owner \n2. Invitee (Collaborator)\n3. Normal User\n4. Exit")
    choice = input("Enter choice (1-4): ")
    
    if choice == '4':
        print("Exiting...")
        return
    token_files = ["owner_token.txt", "collab_token.txt", "external_token.txt"]

    output_path = token_files[int(choice) - 1]

    # Create the MSAL app
    app = PublicClientApplication(
        config.CLIENT_ID,
        authority=config.AUTHORITY_URL
    )

    scopes = config.SCOPES
    print("Opening browser for authentication...")
    result = app.acquire_token_interactive(scopes=scopes)

    if "access_token" in result:
        print("\nSUCCESS! Got access token!")
        print(f"Token (first 50 chars): {result['access_token'][:50]}...")

        with open(output_path, 'w') as f:
            f.write(result['access_token'])
        print(f"Token saved to {output_path}")
        print("\nYou're ready to test OneDrive API!")
    else:
        print("\nERROR getting token:")
        print(f"Error: {result.get('error')}")
        print(f"Description: {result.get('error_description')}")


if __name__ == "__main__":
    main()
