#!/usr/bin/env python3
"""
LLM Service for A2A Math Agent
Supports OpenAI, Anthropic, and Gemini with fallback to deterministic calculations
"""

import os
import asyncio
from typing import Optional, Dict, Any, Union
from enum import Enum
import logging

# LLM client imports
try:
    import openai
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    from anthropic import Anthropic, AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    NONE = "none"


class LLMConfig:
    """Configuration for LLM providers."""
    
    def __init__(self):
        # OpenAI Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Anthropic Configuration
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        
        # Gemini Configuration
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        # General Configuration
        self.preferred_provider = LLMProvider(os.getenv("LLM_PROVIDER", "none").lower())
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "150"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    
    def is_provider_configured(self, provider: LLMProvider) -> bool:
        """Check if a provider is properly configured."""
        if provider == LLMProvider.OPENAI:
            return OPENAI_AVAILABLE and bool(self.openai_api_key)
        elif provider == LLMProvider.ANTHROPIC:
            return ANTHROPIC_AVAILABLE and bool(self.anthropic_api_key)
        elif provider == LLMProvider.GEMINI:
            return GEMINI_AVAILABLE and bool(self.gemini_api_key)
        return False
    
    def get_available_providers(self) -> list[LLMProvider]:
        """Get list of available and configured providers."""
        providers = []
        for provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC, LLMProvider.GEMINI]:
            if self.is_provider_configured(provider):
                providers.append(provider)
        return providers


class LLMService:
    """Service for handling LLM requests with multiple provider support."""
    
    def __init__(self):
        self.config = LLMConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize clients
        self.openai_client = None
        self.anthropic_client = None
        self.gemini_model = None
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients based on configuration."""
        try:
            # Initialize OpenAI
            if self.config.is_provider_configured(LLMProvider.OPENAI):
                self.openai_client = OpenAI(api_key=self.config.openai_api_key)
                self.logger.info("OpenAI client initialized")
            
            # Initialize Anthropic
            if self.config.is_provider_configured(LLMProvider.ANTHROPIC):
                self.anthropic_client = Anthropic(api_key=self.config.anthropic_api_key)
                self.logger.info("Anthropic client initialized")
            
            # Initialize Gemini
            if self.config.is_provider_configured(LLMProvider.GEMINI):
                genai.configure(api_key=self.config.gemini_api_key)
                self.gemini_model = genai.GenerativeModel(self.config.gemini_model)
                self.logger.info("Gemini client initialized")
                
        except Exception as e:
            self.logger.error(f"Error initializing LLM clients: {e}")
    
    def is_llm_available(self) -> bool:
        """Check if any LLM provider is available."""
        return len(self.config.get_available_providers()) > 0
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all LLM providers."""
        return {
            "preferred_provider": self.config.preferred_provider.value,
            "available_providers": [p.value for p in self.config.get_available_providers()],
            "openai_configured": self.config.is_provider_configured(LLMProvider.OPENAI),
            "anthropic_configured": self.config.is_provider_configured(LLMProvider.ANTHROPIC),
            "gemini_configured": self.config.is_provider_configured(LLMProvider.GEMINI),
            "fallback_enabled": True
        }
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a mathematical assistant. Solve math problems step by step and provide clear, concise answers. Focus on accuracy and show your work when helpful."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API."""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")
        
        try:
            response = self.anthropic_client.messages.create(
                model=self.config.anthropic_model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system="You are a mathematical assistant. Solve math problems step by step and provide clear, concise answers. Focus on accuracy and show your work when helpful.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text.strip()
        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            raise
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API."""
        if not self.gemini_model:
            raise ValueError("Gemini model not initialized")
        
        try:
            full_prompt = f"""You are a mathematical assistant. Solve math problems step by step and provide clear, concise answers. Focus on accuracy and show your work when helpful.

User question: {prompt}"""
            
            response = self.gemini_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                )
            )
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"Gemini API error: {e}")
            raise
    
    async def generate_response(self, prompt: str, provider: Optional[LLMProvider] = None) -> str:
        """
        Generate response using specified or preferred LLM provider.
        
        Args:
            prompt: The mathematical question or problem
            provider: Specific provider to use (optional)
            
        Returns:
            Response from the LLM
            
        Raises:
            ValueError: If no LLM providers are available
        """
        # Determine which provider to use
        target_provider = provider or self.config.preferred_provider
        available_providers = self.config.get_available_providers()
        
        if not available_providers:
            raise ValueError("No LLM providers are configured or available")
        
        # If preferred provider is not available, use the first available one
        if target_provider not in available_providers:
            target_provider = available_providers[0]
            self.logger.warning(f"Preferred provider not available, using {target_provider.value}")
        
        # Call the appropriate provider
        try:
            if target_provider == LLMProvider.OPENAI:
                return await self._call_openai(prompt)
            elif target_provider == LLMProvider.ANTHROPIC:
                return await self._call_anthropic(prompt)
            elif target_provider == LLMProvider.GEMINI:
                return await self._call_gemini(prompt)
            else:
                raise ValueError(f"Unsupported provider: {target_provider}")
                
        except Exception as e:
            self.logger.error(f"Error with {target_provider.value}: {e}")
            
            # Try fallback to other providers
            for fallback_provider in available_providers:
                if fallback_provider != target_provider:
                    try:
                        self.logger.info(f"Trying fallback provider: {fallback_provider.value}")
                        if fallback_provider == LLMProvider.OPENAI:
                            return await self._call_openai(prompt)
                        elif fallback_provider == LLMProvider.ANTHROPIC:
                            return await self._call_anthropic(prompt)
                        elif fallback_provider == LLMProvider.GEMINI:
                            return await self._call_gemini(prompt)
                    except Exception as fallback_error:
                        self.logger.error(f"Fallback {fallback_provider.value} also failed: {fallback_error}")
                        continue
            
            # If all providers fail, re-raise the original error
            raise e