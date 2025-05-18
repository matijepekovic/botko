class AIProvider:
    """Base class for AI content generation providers"""
    def __init__(self, api_key):
        self.api_key = api_key
    
    def generate_content(self, prompt, max_tokens=700, temperature=0.7):
        """Generate content using the AI provider"""
        raise NotImplementedError("Subclasses must implement this method")


class OpenAIProvider(AIProvider):
    """OpenAI (GPT) implementation"""
    def generate_content(self, prompt, max_tokens=700, temperature=0.7):
        import openai
        
        openai.api_key = self.api_key
        
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


class GeminiProvider(AIProvider):
    """Google Gemini implementation"""
    def generate_content(self, prompt, max_tokens=700, temperature=0.7):
        import google.generativeai as genai
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
        )
        
        return response.text


class ClaudeProvider(AIProvider):
    """Anthropic Claude implementation"""
    def generate_content(self, prompt, max_tokens=700, temperature=0.7):
        import anthropic
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
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


# Factory function to get the appropriate provider
def get_provider(provider_name, api_key):
    """Return the appropriate AI provider based on name"""
    providers = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "claude": ClaudeProvider
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}. Available providers: {', '.join(providers.keys())}")
    
    return providers[provider_name](api_key)