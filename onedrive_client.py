# onedrive_client.py
"""
OneDrive API Client

Wrapper for Microsoft Graph API calls to OneDrive
"""

import requests
import json


class OneDriveClient:
    """Client for OneDrive REST API operations"""
    
    def __init__(self, access_token):
        """
        Initialize OneDrive client
        
        Args:
            access_token: Microsoft Graph API access token
        """
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def get_user_info(self):
        """Get current user information"""
        url = f"{self.base_url}/me"
        response = requests.get(url, headers=self.headers)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code == 200 else {}
        }
    
    def list_files(self):
        """List all files in user's OneDrive root"""
        url = f"{self.base_url}/me/drive/root/children"
        response = requests.get(url, headers=self.headers)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code == 200 else {}
        }
    
    def create_file(self, filename, content):
        """
        Create a file in OneDrive
        
        Args:
            filename: Name of file to create
            content: File content (string or bytes)
        
        Returns:
            Dictionary with status_code and file data
        """
        url = f"{self.base_url}/me/drive/root:/{filename}:/content"
        
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        response = requests.put(url, headers=self.headers, data=content)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code in [200, 201] else {}
        }
    
    def read_file(self, file_id):
        """
        Read file metadata
        
        Args:
            file_id: OneDrive file ID
        
        Returns:
            Dictionary with status_code and file metadata
        """
        url = f"{self.base_url}/me/drive/items/{file_id}"
        response = requests.get(url, headers=self.headers)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code == 200 else {}
        }

    def read_file_via_share(self, share_id):
        """
        Read file metadata using a sharing link (shareId or encoded URL).
        """
        url = f"{self.base_url}/shares/{share_id}/driveItem"
        response = requests.get(url, headers=self.headers)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code == 200 else {}
        }
    
    def update_file(self, file_id, content):
        """
        Update file content
        
        Args:
            file_id: OneDrive file ID
            content: New file content
        
        Returns:
            Dictionary with status_code
        """
        url = f"{self.base_url}/me/drive/items/{file_id}/content"
        
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        response = requests.put(url, headers=self.headers, data=content)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.text else {}
        }

    def update_file_via_share(self, share_id, content):
        """
        Update file content using a sharing link (shareId or encoded URL).
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        url = f"{self.base_url}/shares/{share_id}/driveItem/content"
        response = requests.put(url, headers=self.headers, data=content)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.text else {}
        }
    
    def delete_file(self, file_id):
        """
        Delete a file
        
        Args:
            file_id: OneDrive file ID
        
        Returns:
            Dictionary with status_code
        """
        url = f"{self.base_url}/me/drive/items/{file_id}"
        response = requests.delete(url, headers=self.headers)
        return {
            'status_code': response.status_code
        }

    def delete_file_via_share(self, share_id):
        """
        Delete a file using a sharing link (shareId or encoded URL).
        """
        url = f"{self.base_url}/shares/{share_id}/driveItem"
        response = requests.delete(url, headers=self.headers)
        return {
            'status_code': response.status_code
        }
    
    def share_file(self, file_id, link_type='view', scope='anonymous'):
        """
        Share a file (create sharing link)
        
        Args:
            file_id: OneDrive file ID
            link_type: Type of sharing link ('view', 'edit', 'embed')
            scope: 'anonymous' (personal use case) or 'organization'
        
        Returns:
            Dictionary with status_code and sharing link
        """
        url = f"{self.base_url}/me/drive/items/{file_id}/createLink"
        
        payload = {
            "type": link_type,
            "scope": scope
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code in [200, 201] else {}
        }

    def share_file_via_share(self, share_id, link_type='view', scope='anonymous'):
        """
        Create a sharing link using an existing shareId/encoded URL context.
        """
        url = f"{self.base_url}/shares/{share_id}/driveItem/createLink"
        payload = {
            "type": link_type,
            "scope": scope
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code in [200, 201] else {}
        }

    def invite_user(self, file_id, emails, role='write', send_invitation=True, require_sign_in=True, message=None):
        """
        Share a file directly with specific users (invite).
        
        Args:
            file_id: OneDrive file ID
            emails: List of email addresses to invite
            role: Permission role ('read' or 'write')
            send_invitation: Whether to send an email invitation
            require_sign_in: Whether sign-in is required to access
            message: Optional message to include
        
        Returns:
            Dictionary with status_code and invite response
        """
        url = f"{self.base_url}/me/drive/items/{file_id}/invite"
        recipients = [{"email": email} for email in emails]
        payload = {
            "recipients": recipients,
            "requireSignIn": require_sign_in,
            "sendInvitation": send_invitation,
            "roles": [role]
        }
        if message:
            payload["message"] = message

        response = requests.post(url, headers=self.headers, json=payload)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.text else {}
        }
    
    def get_file_permissions(self, file_id):
        """
        Get permissions for a file
        
        Args:
            file_id: OneDrive file ID
        
        Returns:
            Dictionary with permissions data
        """
        url = f"{self.base_url}/me/drive/items/{file_id}/permissions"
        response = requests.get(url, headers=self.headers)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code == 200 else {}
        }


# Test the client
if __name__ == "__main__":
    print("OneDrive Client Test")
    print("\nTo test this client:")
    print("1. Make sure you have a valid token in token.txt")
    print("2. Run: python test_onedrive.py")
