"""
LLM - LLM integrations for FlowAgent.

This module provides integrations with popular LLM providers.

Design principle: **Open pass-through**. Any model name is accepted and
passed directly to the API. No hardcoded model lists that become stale.

Users can register custom aliases via ModelRegistry for convenience:

    from flowagent.core.models import get_registry
    registry = get_registry()
    registry.register_alias("my-gpt", "gpt-5.5", provider="openai")

    # Then use the alias
    llm = OpenAI(model="my-gpt")  # resolves to "gpt-5.5" via registry
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypeVar, Union, AsyncIterator

from flowagent.core.logger import logger
from flowagent.core.exceptions import IntegrationError, AuthenticationError

T = TypeVar("T")


def _resolve_model(model: str) -> str:
    """
    Resolve a model name through the global registry.

    If the name is a registered alias, returns the resolved name.
    Otherwise, returns the name as-is (pass-through).

    Args:
        model: Model name or alias

    Returns:
        Resolved model name
    """
    try:
        from flowagent.core.models import get_registry
        return get_registry().get_model(model)
    except Exception:
        # If registry is not available, pass through
        return model


@dataclass
class LLMMessage:
    """A message in an LLM conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class LLMResponse:
    """Response from an LLM."""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    tool_calls: Optional[List[Dict[str, Any]]] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMConfig:
    """
    Configuration for an LLM provider.

    The `model` field accepts ANY model name. It is passed directly to the
    API without validation. If the name matches a registered alias in
    ModelRegistry, it will be resolved automatically.
    """
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    timeout: float = 60.0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM integrations should inherit from this class.
    Providers accept ANY model name and pass it through to the API.
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        # Resolve model alias at init time
        self.config.model = _resolve_model(self.config.model)

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat request to the LLM."""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a chat response from the LLM."""
        pass

    @abstractmethod
    async def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        pass

    def _prepare_messages(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Prepare messages for API call."""
        prepared = []
        if system_prompt:
            prepared.append({"role": "system", "content": system_prompt})
        for msg in messages:
            prepared.append({"role": msg.role, "content": msg.content})
        return prepared


class OpenAI(LLMProvider):
    """
    OpenAI LLM provider.

    Accepts ANY model name. Passes it directly to the OpenAI API.
    Common models: gpt-5.5, gpt-5, gpt-4.1, gpt-4o, o4-mini, o3, etc.

    Example:
        >>> llm = OpenAI(model="gpt-5.5")
        >>> # Or use any custom/fine-tuned model:
        >>> llm = OpenAI(model="ft:gpt-4.1:my-org:my-suffix")
        >>> # Or use a registered alias:
        >>> llm = OpenAI(model="my-custom-alias")
    """

    def __init__(self, config: Optional[LLMConfig] = None, **kwargs):
        if config is None:
            config = LLMConfig(**kwargs)
        super().__init__(config)

        try:
            import openai
            self._client = openai.AsyncOpenAI(
                api_key=config.api_key,
                base_url=config.api_base,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        except ImportError:
            raise IntegrationError(
                "OpenAI package not installed. "
                "Install this local package with the llm extra: pip install -e '.[llm]'"
            )

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat request to OpenAI."""
        try:
            prepared_messages = self._prepare_messages(messages)
            params = {
                "model": self.config.model,
                "messages": prepared_messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                "frequency_penalty": self.config.frequency_penalty,
                "presence_penalty": self.config.presence_penalty,
            }
            if self.config.stop:
                params["stop"] = self.config.stop
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            params.update(kwargs)

            response = await self._client.chat.completions.create(**params)
            choice = response.choices[0]
            message = choice.message

            return LLMResponse(
                content=message.content or "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                tool_calls=message.tool_calls,
                finish_reason=choice.finish_reason,
            )
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise IntegrationError(f"OpenAI chat failed: {e}") from e

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a chat response from OpenAI."""
        try:
            prepared_messages = self._prepare_messages(messages)
            params = {
                "model": self.config.model,
                "messages": prepared_messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "stream": True,
            }
            if tools:
                params["tools"] = tools
            params.update(kwargs)

            stream = await self._client.chat.completions.create(**params)
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI stream error: {e}")
            raise IntegrationError(f"OpenAI stream failed: {e}") from e

    async def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI."""
        try:
            response = await self._client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI embeddings error: {e}")
            raise IntegrationError(f"OpenAI embeddings failed: {e}") from e


class Anthropic(LLMProvider):
    """
    Anthropic LLM provider.

    Accepts ANY model name. Passes it directly to the Anthropic API.
    Common models: claude-opus-4-7, claude-sonnet-4-6, claude-haiku-4-5, etc.

    Example:
        >>> llm = Anthropic(model="claude-opus-4-7")
        >>> # Or use a registered alias:
        >>> llm = Anthropic(model="opus")  # if registered in ModelRegistry
    """

    def __init__(self, config: Optional[LLMConfig] = None, **kwargs):
        if config is None:
            config = LLMConfig(**kwargs)
        super().__init__(config)

        try:
            import anthropic
            self._client = anthropic.AsyncAnthropic(
                api_key=config.api_key,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        except ImportError:
            raise IntegrationError(
                "Anthropic package not installed. "
                "Install this local package with the llm extra: pip install -e '.[llm]'"
            )

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat request to Anthropic."""
        try:
            system_message = None
            chat_messages = []
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    chat_messages.append({"role": msg.role, "content": msg.content})

            params = {
                "model": self.config.model,
                "messages": chat_messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }
            if system_message:
                params["system"] = system_message
            if tools:
                params["tools"] = tools
            params.update(kwargs)

            response = await self._client.messages.create(**params)
            return LLMResponse(
                content=response.content[0].text if response.content else "",
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                finish_reason=response.stop_reason,
            )
        except Exception as e:
            logger.error(f"Anthropic chat error: {e}")
            raise IntegrationError(f"Anthropic chat failed: {e}") from e

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a chat response from Anthropic."""
        try:
            system_message = None
            chat_messages = []
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    chat_messages.append({"role": msg.role, "content": msg.content})

            params = {
                "model": self.config.model,
                "messages": chat_messages,
                "max_tokens": self.config.max_tokens,
                "stream": True,
            }
            if system_message:
                params["system"] = system_message
            params.update(kwargs)

            async with self._client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Anthropic stream error: {e}")
            raise IntegrationError(f"Anthropic stream failed: {e}") from e

    async def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Anthropic doesn't support embeddings."""
        raise IntegrationError("Anthropic does not support embeddings")


class GoogleAI(LLMProvider):
    """
    Google AI LLM provider.

    Accepts ANY model name. Passes it directly to the Google AI API.
    Common models: gemini-2.5-pro, gemini-2.5-flash, etc.

    Example:
        >>> llm = GoogleAI(model="gemini-2.5-pro")
    """

    def __init__(self, config: Optional[LLMConfig] = None, **kwargs):
        if config is None:
            config = LLMConfig(**kwargs)
        super().__init__(config)

        try:
            import google.generativeai as genai
            genai.configure(api_key=config.api_key)
            self._model = genai.GenerativeModel(config.model)
        except ImportError:
            raise IntegrationError(
                "Google AI package not installed. "
                "Install this local package with the llm extra: pip install -e '.[llm]'"
            )

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat request to Google AI."""
        try:
            history = []
            for msg in messages[:-1]:
                history.append({
                    "role": "user" if msg.role == "user" else "model",
                    "parts": [msg.content],
                })

            chat = self._model.start_chat(history=history)
            response = await chat.send_message_async(messages[-1].content)

            return LLMResponse(
                content=response.text,
                model=self.config.model,
                usage={
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                },
            )
        except Exception as e:
            logger.error(f"Google AI chat error: {e}")
            raise IntegrationError(f"Google AI chat failed: {e}") from e

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a chat response from Google AI."""
        try:
            history = []
            for msg in messages[:-1]:
                history.append({
                    "role": "user" if msg.role == "user" else "model",
                    "parts": [msg.content],
                })

            chat = self._model.start_chat(history=history)
            response = await chat.send_message_async(
                messages[-1].content, stream=True,
            )
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Google AI stream error: {e}")
            raise IntegrationError(f"Google AI stream failed: {e}") from e

    async def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Google AI."""
        try:
            import google.generativeai as genai
            embeddings = []
            for text in texts:
                result = await genai.embed_content_async(
                    model="models/embedding-001", content=text,
                )
                embeddings.append(result["embedding"])
            return embeddings
        except Exception as e:
            logger.error(f"Google AI embeddings error: {e}")
            raise IntegrationError(f"Google AI embeddings failed: {e}") from e


class Mistral(LLMProvider):
    """
    Mistral AI LLM provider.

    Accepts ANY model name. Passes it directly to the Mistral API.
    Common models: mistral-large-latest, codestral-latest, etc.

    Example:
        >>> llm = Mistral(model="mistral-large-latest")
    """

    def __init__(self, config: Optional[LLMConfig] = None, **kwargs):
        if config is None:
            config = LLMConfig(**kwargs)
        super().__init__(config)

        try:
            from mistralai.async_client import MistralAsyncClient
            self._client = MistralAsyncClient(api_key=config.api_key)
        except ImportError:
            raise IntegrationError(
                "Mistral AI package not installed. "
                "Install this local package with the llm extra: pip install -e '.[llm]'"
            )

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat request to Mistral."""
        try:
            prepared_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]
            response = await self._client.chat(
                model=self.config.model,
                messages=prepared_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            )
        except Exception as e:
            logger.error(f"Mistral chat error: {e}")
            raise IntegrationError(f"Mistral chat failed: {e}") from e

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a chat response from Mistral."""
        try:
            prepared_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]
            stream = await self._client.chat_stream(
                model=self.config.model,
                messages=prepared_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Mistral stream error: {e}")
            raise IntegrationError(f"Mistral stream failed: {e}") from e

    async def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Mistral."""
        try:
            response = await self._client.embeddings(
                model="mistral-embed", input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Mistral embeddings error: {e}")
            raise IntegrationError(f"Mistral embeddings failed: {e}") from e


class Ollama(LLMProvider):
    """
    Ollama LLM provider for local models.

    Accepts ANY model name that is available in your local Ollama instance.

    Example:
        >>> llm = Ollama(model="llama3.1:70b")
        >>> llm = Ollama(model="qwen2.5:72b")
        >>> llm = Ollama(model="deepseek-r1:671b")
    """

    def __init__(self, config: Optional[LLMConfig] = None, **kwargs):
        if config is None:
            config = LLMConfig(api_base="http://localhost:11434", **kwargs)
        super().__init__(config)

        try:
            import httpx
            self._client = httpx.AsyncClient(
                base_url=config.api_base, timeout=config.timeout,
            )
        except ImportError:
            raise IntegrationError(
                "httpx package not installed. "
                "Install this repository locally with: pip install -e ."
            )

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat request to Ollama."""
        try:
            prepared_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]
            response = await self._client.post(
                "/api/chat",
                json={
                    "model": self.config.model,
                    "messages": prepared_messages,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens,
                    },
                },
            )
            data = response.json()
            return LLMResponse(
                content=data["message"]["content"],
                model=self.config.model,
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                },
            )
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise IntegrationError(f"Ollama chat failed: {e}") from e

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a chat response from Ollama."""
        try:
            prepared_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]
            async with self._client.stream(
                "POST",
                "/api/chat",
                json={
                    "model": self.config.model,
                    "messages": prepared_messages,
                    "stream": True,
                    "options": {
                        "temperature": self.config.temperature,
                        "num_predict": self.config.max_tokens,
                    },
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data:
                            yield data["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            raise IntegrationError(f"Ollama stream failed: {e}") from e

    async def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama."""
        try:
            embeddings = []
            for text in texts:
                response = await self._client.post(
                    "/api/embeddings",
                    json={"model": self.config.model, "prompt": text},
                )
                data = response.json()
                embeddings.append(data["embedding"])
            return embeddings
        except Exception as e:
            logger.error(f"Ollama embeddings error: {e}")
            raise IntegrationError(f"Ollama embeddings failed: {e}") from e


class MiMo(LLMProvider):
    """
    Xiaomi MiMo model provider.

    Supports two modes:
    1. vLLM OpenAI-compatible API (server-backed inference)
    2. Hugging Face transformers (local inference)

    Accepts ANY model name from Hugging Face or your vLLM server.

    Example (vLLM):
        >>> # Start vLLM: vllm serve XiaomiMiMo/MiMo-v2.5-Pro --port 8000
        >>> llm = MiMo(model="XiaomiMiMo/MiMo-v2.5-Pro", api_base="http://localhost:8000/v1")
        >>> # Or use a registered alias:
        >>> llm = MiMo(model="mimo-pro")  # if registered in ModelRegistry

    Example (Hugging Face):
        >>> llm = MiMo(model="XiaomiMiMo/MiMo-v2.5-Pro", mode="hf", device="cuda")
    """

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        mode: str = "vllm",
        device: str = "auto",
        **kwargs,
    ):
        if config is None:
            config = LLMConfig(**kwargs)

        if mode == "vllm" and not config.api_base:
            config.api_base = "http://localhost:8000/v1"

        super().__init__(config)
        self._mode = mode
        self._device = device
        self._hf_model = None
        self._hf_tokenizer = None

        if mode == "vllm":
            self._init_vllm()
        elif mode == "hf":
            self._init_hf()
        else:
            raise IntegrationError(f"Unknown MiMo mode: {mode}. Use 'vllm' or 'hf'.")

    def _init_vllm(self) -> None:
        """Initialize vLLM OpenAI-compatible client."""
        try:
            import openai
            self._client = openai.AsyncOpenAI(
                api_key=self.config.api_key or "dummy",
                base_url=self.config.api_base,
                timeout=self.config.timeout,
                max_retries=self.config.max_retries,
            )
            logger.info(f"MiMo vLLM client initialized: {self.config.api_base}")
        except ImportError:
            raise IntegrationError(
                "openai package not installed. Install with: pip install openai"
            )

    def _init_hf(self) -> None:
        """Initialize Hugging Face model."""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            model_name = self.config.model
            logger.info(f"Loading MiMo model: {model_name}")

            self._hf_tokenizer = AutoTokenizer.from_pretrained(
                model_name, trust_remote_code=True,
            )
            device_map = "auto" if self._device == "auto" else self._device
            self._hf_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.bfloat16,
                device_map=device_map,
                trust_remote_code=True,
            )
            logger.info(f"MiMo HF model loaded: {model_name}")
        except ImportError:
            raise IntegrationError(
                "transformers/torch not installed. "
                "Install with: pip install transformers torch"
            )

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat request to MiMo."""
        if self._mode == "vllm":
            return await self._chat_vllm(messages, tools, **kwargs)
        return await self._chat_hf(messages, **kwargs)

    async def _chat_vllm(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Chat via vLLM OpenAI-compatible API."""
        try:
            prepared_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]
            params = {
                "model": self.config.model,
                "messages": prepared_messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
            }
            if self.config.stop:
                params["stop"] = self.config.stop
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            params.update(kwargs)

            response = await self._client.chat.completions.create(**params)
            choice = response.choices[0]
            message = choice.message

            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return LLMResponse(
                content=message.content or "",
                model=response.model,
                usage=usage,
                tool_calls=message.tool_calls,
                finish_reason=choice.finish_reason,
            )
        except Exception as e:
            logger.error(f"MiMo vLLM chat error: {e}")
            raise IntegrationError(f"MiMo vLLM chat failed: {e}") from e

    async def _chat_hf(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Chat via Hugging Face transformers."""
        try:
            import torch

            prepared_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]
            input_ids = self._hf_tokenizer.apply_chat_template(
                prepared_messages,
                return_tensors="pt",
                add_generation_prompt=True,
            ).to(self._hf_model.device)

            with torch.no_grad():
                outputs = self._hf_model.generate(
                    input_ids,
                    max_new_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    do_sample=self.config.temperature > 0,
                    pad_token_id=self._hf_tokenizer.eos_token_id,
                )

            generated_ids = outputs[0][input_ids.shape[-1]:]
            content = self._hf_tokenizer.decode(generated_ids, skip_special_tokens=True)

            return LLMResponse(
                content=content,
                model=self.config.model,
                usage={
                    "prompt_tokens": input_ids.shape[-1],
                    "completion_tokens": len(generated_ids),
                    "total_tokens": input_ids.shape[-1] + len(generated_ids),
                },
            )
        except Exception as e:
            logger.error(f"MiMo HF chat error: {e}")
            raise IntegrationError(f"MiMo HF chat failed: {e}") from e

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a chat response from MiMo."""
        if self._mode != "vllm":
            raise IntegrationError("Streaming is only supported in vLLM mode")
        try:
            prepared_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]
            params = {
                "model": self.config.model,
                "messages": prepared_messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "stream": True,
            }
            if tools:
                params["tools"] = tools
            params.update(kwargs)

            stream = await self._client.chat.completions.create(**params)
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"MiMo stream error: {e}")
            raise IntegrationError(f"MiMo stream failed: {e}") from e

    async def embeddings(self, texts: List[str]) -> List[List[float]]:
        """MiMo does not natively support embeddings."""
        raise IntegrationError(
            "MiMo does not support embeddings. Use a dedicated embedding model."
        )


class OpenAICompatible(LLMProvider):
    """
    Generic OpenAI-compatible provider.

    Works with ANY API that implements the OpenAI chat completions format:
    vLLM, Ollama (via /v1), LiteLLM, LocalAI, text-generation-inference, etc.

    Example:
        >>> # vLLM server
        >>> llm = OpenAICompatible(
        ...     model="meta-llama/Llama-3-70B-Instruct",
        ...     api_base="http://localhost:8000/v1",
        ... )
        >>> # LiteLLM proxy
        >>> llm = OpenAICompatible(
        ...     model="my-custom-model",
        ...     api_base="http://localhost:4000/v1",
        ...     api_key="sk-...",
        ... )
    """

    def __init__(self, config: Optional[LLMConfig] = None, **kwargs):
        if config is None:
            config = LLMConfig(**kwargs)
        super().__init__(config)

        if not config.api_base:
            raise IntegrationError(
                "api_base is required for OpenAICompatible provider"
            )

        try:
            import openai
            self._client = openai.AsyncOpenAI(
                api_key=config.api_key or "dummy",
                base_url=config.api_base,
                timeout=config.timeout,
                max_retries=config.max_retries,
            )
        except ImportError:
            raise IntegrationError(
                "openai package not installed. Install with: pip install openai"
            )

    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Send a chat request."""
        try:
            prepared_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]
            params = {
                "model": self.config.model,
                "messages": prepared_messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
            params.update(kwargs)

            response = await self._client.chat.completions.create(**params)
            choice = response.choices[0]
            message = choice.message

            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return LLMResponse(
                content=message.content or "",
                model=response.model,
                usage=usage,
                tool_calls=message.tool_calls,
                finish_reason=choice.finish_reason,
            )
        except Exception as e:
            logger.error(f"OpenAICompatible chat error: {e}")
            raise IntegrationError(f"OpenAICompatible chat failed: {e}") from e

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a chat response."""
        try:
            prepared_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]
            params = {
                "model": self.config.model,
                "messages": prepared_messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "stream": True,
            }
            params.update(kwargs)

            stream = await self._client.chat.completions.create(**params)
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAICompatible stream error: {e}")
            raise IntegrationError(f"OpenAICompatible stream failed: {e}") from e

    async def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings."""
        try:
            response = await self._client.embeddings.create(
                model=self.config.model, input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAICompatible embeddings error: {e}")
            raise IntegrationError(f"OpenAICompatible embeddings failed: {e}") from e
