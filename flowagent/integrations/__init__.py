"""
FlowAgent Integrations - Third-party integrations for FlowAgent.

This module provides integrations with popular services and frameworks.
"""

from flowagent.integrations.llm import (
    LLMProvider,
    OpenAI,
    Anthropic,
    GoogleAI,
    Mistral,
    Ollama,
    MiMo,
    OpenAICompatible,
)
from flowagent.integrations.database import (
    DatabaseProvider,
    PostgreSQL,
    MySQL,
    MongoDB,
    Redis,
    Elasticsearch,
)
from flowagent.integrations.cloud import (
    CloudProvider,
    AWS,
    GoogleCloud,
    Azure,
)
from flowagent.integrations.messaging import (
    MessagingProvider,
    Slack,
    Discord,
    Telegram,
    Email,
    Webhook,
)

__all__ = [
    # LLM Providers
    "LLMProvider",
    "OpenAI",
    "Anthropic",
    "GoogleAI",
    "Mistral",
    "Ollama",
    "MiMo",
    "OpenAICompatible",
    # Database Providers
    "DatabaseProvider",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "Elasticsearch",
    # Cloud Providers
    "CloudProvider",
    "AWS",
    "GoogleCloud",
    "Azure",
    # Messaging Providers
    "MessagingProvider",
    "Slack",
    "Discord",
    "Telegram",
    "Email",
    "Webhook",
]
