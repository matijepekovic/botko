"""
Authentication service for managing API credentials.
"""

import webbrowser
from typing import Dict, Any, Optional

from ..core.database import db
from ..core.linkedin_api import linkedin_api

class AuthService:
    """Service for handling authentication and credentials."""
    
    @staticmethod
    def set_linkedin_credentials(client_id: str, client_secret: str) -> None:
        """
        Set LinkedIn API credentials.
        
        Args:
            client_id: LinkedIn client ID
            client_secret: LinkedIn client secret
        """
        linkedin_api.set_credentials(client_id, client_secret)
    
    @staticmethod
    def is_linkedin_configured() -> bool:
        """
        Check if LinkedIn API credentials are configured.
        
        Returns:
            Boolean indicating if credentials are set
        """
        client_id = db.get_credential('linkedin', 'client_id')
        client_secret = db.get_credential('linkedin', 'client_secret')
        
        return bool(client_id) and bool(client_secret)
    
    @staticmethod
    def is_linkedin_authenticated() -> bool:
        """
        Check if we have a valid LinkedIn access token.
        
        Returns:
            Boolean indicating authentication status
        """
        return linkedin_api.is_authenticated()
    
    @staticmethod
    def start_linkedin_auth_flow(redirect_uri: str = "http://localhost:8000/callback") -> str:
        """
        Start the LinkedIn authorization flow.
        
        Args:
            redirect_uri: Redirect URI for the OAuth flow
            
        Returns:
            The authorization URL
        """
        return linkedin_api.start_manual_auth_flow(redirect_uri)
    
    @staticmethod
    def complete_linkedin_auth_flow(auth_code: str, redirect_uri: str = "http://localhost:8000/callback") -> str:
        """
        Complete the LinkedIn authorization flow.
        
        Args:
            auth_code: Authorization code from the redirect
            redirect_uri: Redirect URI matching the one used to start the flow
            
        Returns:
            The access token
        """
        return linkedin_api.complete_manual_auth_flow(auth_code, redirect_uri)
    
    @staticmethod
    def set_ai_provider_key(provider_name: str, api_key: str) -> None:
        """
        Save an API key for an AI provider.
        
        Args:
            provider_name: Name of the provider ('openai', 'gemini', or 'claude')
            api_key: API key to save
        """
        db.set_credential(provider_name, 'api_key', api_key)
    
    @staticmethod
    def get_ai_provider_key(provider_name: str) -> Optional[str]:
        """
        Get an API key for an AI provider.
        
        Args:
            provider_name: Name of the provider ('openai', 'gemini', or 'claude')
            
        Returns:
            API key or None if not found
        """
        return db.get_credential(provider_name, 'api_key')
    
    @staticmethod
    def is_ai_provider_configured(provider_name: str) -> bool:
        """
        Check if an AI provider is configured.
        
        Args:
            provider_name: Name of the provider ('openai', 'gemini', or 'claude')
            
        Returns:
            Boolean indicating if the API key is set
        """
        return bool(AuthService.get_ai_provider_key(provider_name))