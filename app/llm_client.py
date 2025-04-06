import os
import json
import requests
from openai import OpenAI

class LLMClientFactory:
    """Factory class to create the appropriate LLM client based on environment settings."""
    
    @staticmethod
    def get_client():
        """
        Returns the appropriate LLM client based on the LLM_ENGINE environment variable.
        Default is local Ollama if not specified.
        """
        engine = os.environ.get('LLM_ENGINE', 'local').lower()
        
        if engine == 'openai':
            return OpenAIClient()
        else:
            return OllamaClient()

class OpenAIClient:
    """Client for OpenAI API."""
    
    def __init__(self):
        self.client = OpenAI()
    
    def chat_completion(self, system_prompt, user_prompt, model="gpt-3.5-turbo", max_tokens=1000, temperature=0.3):
        """
        Call OpenAI's chat completion API.
        
        Args:
            system_prompt: The system message to set context
            user_prompt: The user's input/question
            model: The OpenAI model to use
            max_tokens: Maximum number of tokens in the response
            temperature: Controls randomness (0-1)
            
        Returns:
            The generated text response
        """
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content.strip()

class OllamaClient:
    """Client for local Ollama API."""
    
    def __init__(self):
        self.base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = os.environ.get('OLLAMA_MODEL', 'llama3:8b')
    
    def chat_completion(self, system_prompt, user_prompt, model=None, max_tokens=1000, temperature=0.3):
        """
        Call Ollama's chat completion API.
        
        Args:
            system_prompt: The system message to set context
            user_prompt: The user's input/question
            model: Override the default Ollama model
            max_tokens: Maximum number of tokens in the response
            temperature: Controls randomness (0-1)
            
        Returns:
            The generated text response
        """
        if model is None:
            model = self.model
            
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            },
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get('message', {}).get('content', '')
            
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama API: {str(e)}")
            # Fallback to simple API if chat API fails
            return self.generate(system_prompt + "\n\n" + user_prompt, model, max_tokens, temperature)
    
    def generate(self, prompt, model=None, max_tokens=1000, temperature=0.3):
        """
        Fallback method to use Ollama's generate API.
        
        Args:
            prompt: The combined prompt
            model: Override the default Ollama model
            max_tokens: Maximum number of tokens in the response
            temperature: Controls randomness (0-1)
            
        Returns:
            The generated text response
        """
        if model is None:
            model = self.model
            
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            },
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
            
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama API: {str(e)}")
            return "Error: Unable to generate response from local LLM."