"""
AI Providers module for content generation.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import json
import os

from .database import db

class AIProvider(ABC):
    """
    Abstract base class for AI content generation providers.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI provider with an API key.
        
        Args:
            api_key: API key for the provider's service
        """
        self.api_key = api_key
        
        # If no API key was provided, try to get it from the database
        if not self.api_key:
            self.api_key = db.get_credential(self.provider_name(), 'api_key')
    
    @classmethod
    @abstractmethod
    def provider_name(cls) -> str:
        """
        Get the name of the provider.
        
        Returns:
            Provider name
        """
        pass
    
    @abstractmethod
    def generate_content(self, prompt: str, max_tokens: int = 700, temperature: float = 0.7) -> str:
        """
        Generate content using the AI provider.
        
        Args:
            prompt: The prompt for content generation
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0 to 1.0)
            
        Returns:
            Generated content
        """
        pass
    
    def save_api_key(self, api_key: str) -> None:
        """
        Save the API key to the database.
        
        Args:
            api_key: API key to save
        """
        self.api_key = api_key
        db.set_credential(self.provider_name(), 'api_key', api_key)


class OpenAIProvider(AIProvider):
    """
    OpenAI (GPT) implementation.
    """
    
    @classmethod
    def provider_name(cls) -> str:
        return "openai"
    
    def generate_content(self, prompt: str, max_tokens: int = 700, temperature: float = 0.7) -> str:
        """
        Generate content using OpenAI's GPT.
        
        Args:
            prompt: The prompt for content generation
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0 to 1.0)
            
        Returns:
            Generated content
        """
        try:
            import openai
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not set. Use save_api_key() first.")
        
        openai.api_key = self.api_key
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert sales consultant with years of experience in home sales."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI generation failed: {str(e)}")


class GeminiProvider(AIProvider):
    """
    Google Gemini implementation.
    """
    
    @classmethod
    def provider_name(cls) -> str:
        return "gemini"
    
    def generate_content(self, prompt: str, max_tokens: int = 700, temperature: float = 0.7) -> str:
        """
        Generate content using Google's Gemini.
        
        Args:
            prompt: The prompt for content generation
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0 to 1.0)
            
        Returns:
            Generated content
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Google Generative AI package not installed. Run: pip install google-generativeai")
        
        if not self.api_key:
            raise ValueError("Gemini API key not set. Use save_api_key() first.")
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )
            
            return response.text
        except Exception as e:
            raise Exception(f"Gemini generation failed: {str(e)}")


class ClaudeProvider(AIProvider):
    """
    Anthropic Claude implementation.
    """
    
    @classmethod
    def provider_name(cls) -> str:
        return "claude"
    
    def generate_content(self, prompt: str, max_tokens: int = 700, temperature: float = 0.7) -> str:
        """
        Generate content using Anthropic's Claude.
        
        Args:
            prompt: The prompt for content generation
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0 to 1.0)
            
        Returns:
            Generated content
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")
        
        if not self.api_key:
            raise ValueError("Claude API key not set. Use save_api_key() first.")
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        try:
            response = client.messages.create(
                model="claude-3-7-sonnet-20250219",  # Updated to the latest Claude model as of May 2025
                max_tokens=max_tokens,
                temperature=temperature,
                system="You are an expert real estate marketing consultant with years of experience in home sales.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Claude generation failed: {str(e)}")


def get_provider(provider_name: str, api_key: Optional[str] = None) -> AIProvider:
    """
    Factory function to get the appropriate AI provider.
    
    Args:
        provider_name: Name of the provider ('openai', 'gemini', or 'claude')
        api_key: Optional API key (if not provided, will try to load from database)
        
    Returns:
        AIProvider instance
    """
    providers = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "claude": ClaudeProvider
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}. Available providers: {', '.join(providers.keys())}")
    
    return providers[provider_name](api_key)


def save_provider_api_key(provider_name: str, api_key: str) -> None:
    """
    Save an API key for a provider.
    
    Args:
        provider_name: Name of the provider
        api_key: API key to save
    """
    provider = get_provider(provider_name)
    provider.save_api_key(api_key)