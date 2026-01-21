import httpx
import json
from typing import AsyncGenerator, Optional
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models.llm_provider import LLMProvider, ProviderType

settings = get_settings()


class UnifiedLLMService:
    """Unified LLM service supporting multiple OpenAI-compatible providers."""

    def __init__(self):
        # Fallback settings when no database provider is configured
        self._fallback_base_url = settings.ollama_base_url
        self._fallback_model = settings.ollama_model

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate text from the LLM with streaming.

        Uses OpenAI-compatible chat/completions endpoint for all providers.
        """
        # Determine provider settings
        if provider:
            base_url = provider.base_url.rstrip('/')
            model_name = model or provider.default_model
            provider_type = provider.provider_type
        else:
            # Fallback to config settings (legacy Ollama support)
            base_url = self._fallback_base_url
            model_name = model or self._fallback_model
            provider_type = ProviderType.OLLAMA

        if not model_name:
            raise ValueError("No model specified and no default model configured")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build OpenAI-compatible payload
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Determine endpoint URL based on provider type
        endpoint_url = self._get_chat_endpoint(base_url, provider_type)

        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                endpoint_url,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    print(f"[DEBUG] Raw line: {line[:300] if line else '(empty)'}")
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                # Try delta first (streaming format)
                                delta = choice.get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                                # Fallback to message format (some providers use this)
                                elif "message" in choice and "content" in choice["message"]:
                                    yield choice["message"]["content"]
                        except json.JSONDecodeError:
                            continue
                    elif line and not line.startswith(":"):
                        # Handle non-SSE format (some providers use NDJSON)
                        try:
                            data = json.loads(line)
                            if "choices" in data and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                # Try delta first (streaming format)
                                delta = choice.get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                                # Fallback to message format (some providers use this)
                                elif "message" in choice and "content" in choice["message"]:
                                    yield choice["message"]["content"]
                            # Also handle message format (Ollama native)
                            elif "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
    ) -> str:
        """Generate text from the LLM without streaming."""
        print(f"[DEBUG] llm_service.generate() called, max_tokens={max_tokens}")
        full_response = ""
        token_count = 0
        async for token in self.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=provider,
            model=model,
        ):
            token_count += 1
            full_response += token
        print(f"[DEBUG] llm_service.generate() finished, tokens={token_count}, response_len={len(full_response)}")
        return full_response

    async def list_models(self, provider: Optional[LLMProvider] = None) -> list[dict]:
        """List available models from a provider."""
        if provider:
            base_url = provider.base_url.rstrip('/')
            provider_type = provider.provider_type
        else:
            base_url = self._fallback_base_url
            provider_type = ProviderType.OLLAMA

        models_url = self._get_models_endpoint(base_url, provider_type)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(models_url)
            response.raise_for_status()
            data = response.json()

            # Handle different response formats
            if "data" in data:
                # OpenAI format
                return data["data"]
            elif "models" in data:
                # Ollama native format
                return data["models"]
            else:
                return []

    async def health_check(self, provider: Optional[LLMProvider] = None) -> bool:
        """Check if a provider is available."""
        try:
            if provider:
                base_url = provider.base_url.rstrip('/')
                provider_type = provider.provider_type
            else:
                base_url = self._fallback_base_url
                provider_type = ProviderType.OLLAMA

            models_url = self._get_models_endpoint(base_url, provider_type)

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(models_url)
                return response.status_code == 200
        except Exception:
            return False

    def _get_chat_endpoint(self, base_url: str, provider_type: ProviderType) -> str:
        """Get the chat completions endpoint for a provider."""
        # All providers use OpenAI-compatible endpoints
        if base_url.endswith('/v1'):
            return f"{base_url}/chat/completions"
        else:
            return f"{base_url}/v1/chat/completions"

    def _get_models_endpoint(self, base_url: str, provider_type: ProviderType) -> str:
        """Get the models listing endpoint for a provider."""
        # Try OpenAI-compatible endpoint first
        if base_url.endswith('/v1'):
            return f"{base_url}/models"
        else:
            return f"{base_url}/v1/models"


class ProviderManager:
    """Manager for handling provider selection from database."""

    @staticmethod
    def get_default_provider(db: Session) -> Optional[LLMProvider]:
        """Get the default provider from database."""
        return db.query(LLMProvider).filter(
            LLMProvider.is_default == True,
            LLMProvider.enabled == True
        ).first()

    @staticmethod
    def get_alternate_provider(db: Session) -> Optional[LLMProvider]:
        """Get the alternate provider from database."""
        return db.query(LLMProvider).filter(
            LLMProvider.is_alternate == True,
            LLMProvider.enabled == True
        ).first()

    @staticmethod
    def get_provider_by_id(db: Session, provider_id: int) -> Optional[LLMProvider]:
        """Get a specific provider by ID."""
        return db.query(LLMProvider).filter(
            LLMProvider.id == provider_id,
            LLMProvider.enabled == True
        ).first()

    @staticmethod
    def get_provider_for_generation(
        db: Session,
        use_alternate: bool = False
    ) -> Optional[LLMProvider]:
        """Get the appropriate provider for generation."""
        if use_alternate:
            provider = ProviderManager.get_alternate_provider(db)
            if provider:
                return provider
            # Fall back to default if no alternate configured
        return ProviderManager.get_default_provider(db)


# Singleton instance
llm_service = UnifiedLLMService()

# Legacy compatibility - keep the old class name as alias
LLMService = UnifiedLLMService
