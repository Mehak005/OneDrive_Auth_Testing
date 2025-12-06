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
    
    def share_file(self, file_id, recipient_email=None, link_type='view'):
        """
        Share a file (create sharing link)
        
        Args:
            file_id: OneDrive file ID
            recipient_email: Optional - email to share with
            link_type: Type of sharing link ('view', 'edit', 'embed')
        
        Returns:
            Dictionary with status_code and sharing link
        """
        url = f"{self.base_url}/me/drive/items/{file_id}/createLink"
        
        payload = {
            "type": link_type,
            "scope": "anonymous"  # or "organization" for org-only
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        return {
            'status_code': response.status_code,
            'data': response.json() if response.status_code in [200, 201] else {}
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