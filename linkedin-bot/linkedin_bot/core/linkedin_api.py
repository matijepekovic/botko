"""
LinkedIn API module that handles all interactions with the LinkedIn API.
"""

import os
import time
import webbrowser
import requests
from typing import Dict, Any, Optional
import json
import urllib.parse
from .database import db

class LinkedInAPI:
    """
    Handles LinkedIn API requests and authentication.
    """
    
    def __init__(self):
        """Initialize the LinkedIn API client."""
        self.base_url = "https://api.linkedin.com/v2"
        self.auth_url = "https://www.linkedin.com/oauth/v2"
        
        # Get credentials from database
        self.client_id = db.get_credential('linkedin', 'client_id')
        self.client_secret = db.get_credential('linkedin', 'client_secret')
        self.access_token = db.get_credential('linkedin', 'access_token')
        
        # Set default request headers
        self.headers = {
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }
        
        if self.access_token:
            self.headers["Authorization"] = f"Bearer {self.access_token}"
    
    def is_authenticated(self) -> bool:
        """
        Check if we have a valid access token.
        
        Returns:
            Boolean indicating authentication status
        """
        return bool(self.access_token)
    
    def set_credentials(self, client_id: str, client_secret: str) -> None:
        """
        Set the LinkedIn API credentials.
        
        Args:
            client_id: LinkedIn API client ID
            client_secret: LinkedIn API client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        
        # Store in database
        db.set_credential('linkedin', 'client_id', client_id)
        db.set_credential('linkedin', 'client_secret', client_secret)
    
    def set_access_token(self, access_token: str) -> None:
        """
        Set the LinkedIn access token.
        
        Args:
            access_token: LinkedIn access token
        """
        self.access_token = access_token
        self.headers["Authorization"] = f"Bearer {access_token}"
        
        # Store in database
        db.set_credential('linkedin', 'access_token', access_token)
    
    def get_authorization_url(self, redirect_uri: str) -> str:
        """
        Get the LinkedIn authorization URL.
        
        Args:
            redirect_uri: Redirect URI for OAuth flow
            
        Returns:
            Authorization URL
        """
        if not self.client_id:
            raise ValueError("LinkedIn client ID not set. Use set_credentials() first.")
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "w_member_social r_basicprofile",
            "state": "random_state_string"  # In a real app, use a secure random token
        }
        
        auth_url = f"{self.auth_url}/authorization?{urllib.parse.urlencode(params)}"
        return auth_url
    
    def authorize(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            auth_code: Authorization code from OAuth redirect
            redirect_uri: Redirect URI matching the one used to get the auth code
            
        Returns:
            Dictionary with access token and other OAuth data
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("LinkedIn API credentials not set. Use set_credentials() first.")
        
        token_url = f"{self.auth_url}/accessToken"
        
        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            self.set_access_token(access_token)
            return token_data
        else:
            raise Exception(f"Authorization failed: {response.status_code} - {response.text}")
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user.
        
        Returns:
            Dictionary with user information
        """
        if not self.is_authenticated():
            raise ValueError("Not authenticated. Set access token or authorize first.")
        
        user_info_url = f"{self.base_url}/me"
        response = requests.get(user_info_url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get user info: {response.status_code} - {response.text}")
    
    def create_post(self, post_text: str) -> bool:
        """
        Create a text post on LinkedIn.
        
        Args:
            post_text: Content of the post
            
        Returns:
            Boolean indicating success
        """
        if not self.is_authenticated():
            raise ValueError("Not authenticated. Set access token or authorize first.")
        
        # Get user URN (required for posting)
        user_data = self.get_user_info()
        user_urn = f"urn:li:person:{user_data['id']}"
        
        # Create the post payload
        post_url = f"{self.base_url}/ugcPosts"
        post_data = {
            "author": user_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post_text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # Make the API call to create the post
        response = requests.post(post_url, headers=self.headers, json=post_data)
        
        if response.status_code == 201:
            print("Post created successfully!")
            return True
        else:
            print(f"Error creating post: {response.status_code}")
            print(response.text)
            return False
    
    def start_manual_auth_flow(self, redirect_uri: str = "http://localhost:8000/callback") -> str:
        """
        Start the manual authorization flow by opening a browser for the user to authorize.
        
        Args:
            redirect_uri: The redirect URI for the OAuth flow
            
        Returns:
            The authorization URL opened in the browser
        """
        auth_url = self.get_authorization_url(redirect_uri)
        
        print("\n\n" + "="*80)
        print("Step 1: Visit this URL in your browser and authorize your app:")
        print(auth_url)
        print("="*80 + "\n")
        
        # Open the browser for the user
        webbrowser.open(auth_url)
        
        print("Step 2: After authorization, you'll be redirected to a URL.")
        print("Copy ONLY the 'code' parameter value from the URL.")
        print("Example: If you see http://localhost:8000/callback?code=AQTdPuXg6_9d&state=random_state_string")
        print("        Just copy: AQTdPuXg6_9d")
        
        return auth_url
    
    def complete_manual_auth_flow(self, auth_code: str, redirect_uri: str = "http://localhost:8000/callback") -> str:
        """
        Complete the manual authentication flow with the provided auth code.
        
        Args:
            auth_code: The authorization code obtained from the redirect
            redirect_uri: The redirect URI matching the one used in start_manual_auth_flow
            
        Returns:
            The access token
        """
        token_data = self.authorize(auth_code, redirect_uri)
        access_token = token_data.get("access_token")
        
        print("\nSuccess! Your access token is:")
        print("="*80)
        print(access_token)
        print("="*80 + "\n")
        
        return access_token

# Create a global instance
linkedin_api = LinkedInAPI()