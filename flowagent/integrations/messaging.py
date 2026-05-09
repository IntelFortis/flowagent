"""
Messaging - Messaging integrations for FlowAgent.

This module provides integrations with popular messaging platforms.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TypeVar, Union

from flowagent.core.logger import logger
from flowagent.core.exceptions import IntegrationError

T = TypeVar("T")


@dataclass
class Message:
    """A message to send."""
    content: str
    channel: Optional[str] = None
    subject: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MessagingConfig:
    """Configuration for messaging services."""
    token: str = ""
    webhook_url: str = ""
    channel: str = ""
    username: str = ""
    icon_emoji: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class MessagingProvider(ABC):
    """
    Abstract base class for messaging providers.

    All messaging integrations should inherit from this class.
    """

    def __init__(self, config: MessagingConfig):
        self.config = config

    @abstractmethod
    async def send(self, message: Message) -> bool:
        """
        Send a message.

        Args:
            message: Message to send

        Returns:
            True if sent successfully
        """
        pass

    @abstractmethod
    async def send_to_channel(
        self,
        channel: str,
        content: str,
        **kwargs,
    ) -> bool:
        """
        Send a message to a specific channel.

        Args:
            channel: Channel identifier
            content: Message content
            **kwargs: Additional parameters

        Returns:
            True if sent successfully
        """
        pass


class Slack(MessagingProvider):
    """
    Slack messaging provider.

    Example:
        >>> slack = Slack(token="xoxb-...")
        >>> await slack.send(Message(content="Hello!", channel="#general"))
    """

    def __init__(self, config: Optional[MessagingConfig] = None, **kwargs):
        if config is None:
            config = MessagingConfig(**kwargs)
        super().__init__(config)

        try:
            from slack_sdk.web.async_client import AsyncWebClient
            self._client = AsyncWebClient(token=config.token)
        except ImportError:
            raise IntegrationError(
                "slack-sdk package not installed. "
                "Install with: pip install flowagent[messaging]"
            )

    async def send(self, message: Message) -> bool:
        """Send a message to Slack."""
        try:
            channel = message.channel or self.config.channel

            kwargs = {
                "channel": channel,
                "text": message.content,
            }

            if self.config.username:
                kwargs["username"] = self.config.username

            if self.config.icon_emoji:
                kwargs["icon_emoji"] = self.config.icon_emoji

            if message.attachments:
                kwargs["attachments"] = message.attachments

            await self._client.chat_postMessage(**kwargs)
            logger.info(f"Slack message sent to {channel}")
            return True

        except Exception as e:
            logger.error(f"Slack send error: {e}")
            return False

    async def send_to_channel(
        self,
        channel: str,
        content: str,
        **kwargs,
    ) -> bool:
        """Send a message to a specific Slack channel."""
        message = Message(content=content, channel=channel, **kwargs)
        return await self.send(message)

    async def upload_file(
        self,
        channel: str,
        file_path: str,
        title: Optional[str] = None,
        initial_comment: Optional[str] = None,
    ) -> bool:
        """Upload a file to Slack."""
        try:
            await self._client.files_upload_v2(
                channel=channel,
                file=file_path,
                title=title,
                initial_comment=initial_comment,
            )
            logger.info(f"File uploaded to Slack: {channel}")
            return True

        except Exception as e:
            logger.error(f"Slack upload error: {e}")
            return False


class Discord(MessagingProvider):
    """
    Discord messaging provider.

    Example:
        >>> discord = Discord(token="...")
        >>> await discord.send(Message(content="Hello!", channel="general"))
    """

    def __init__(self, config: Optional[MessagingConfig] = None, **kwargs):
        if config is None:
            config = MessagingConfig(**kwargs)
        super().__init__(config)

        try:
            import discord
            self._client = discord.Client(intents=discord.Intents.default())
        except ImportError:
            raise IntegrationError(
                "discord.py package not installed. "
                "Install with: pip install flowagent[messaging]"
            )

    async def send(self, message: Message) -> bool:
        """Send a message to Discord."""
        try:
            if not self._client.is_ready():
                await self._client.login(self.config.token)

            channel = self._client.get_channel(int(message.channel or self.config.channel))

            if channel:
                kwargs = {"content": message.content}

                if message.attachments:
                    import discord
                    files = []
                    for att in message.attachments:
                        if "url" in att:
                            files.append(discord.File(att["url"]))
                    kwargs["files"] = files

                await channel.send(**kwargs)
                logger.info(f"Discord message sent to {channel.name}")
                return True

            return False

        except Exception as e:
            logger.error(f"Discord send error: {e}")
            return False

    async def send_to_channel(
        self,
        channel: str,
        content: str,
        **kwargs,
    ) -> bool:
        """Send a message to a specific Discord channel."""
        message = Message(content=content, channel=channel, **kwargs)
        return await self.send(message)


class Telegram(MessagingProvider):
    """
    Telegram messaging provider.

    Example:
        >>> telegram = Telegram(token="...")
        >>> await telegram.send(Message(content="Hello!", channel="123456"))
    """

    def __init__(self, config: Optional[MessagingConfig] = None, **kwargs):
        if config is None:
            config = MessagingConfig(**kwargs)
        super().__init__(config)

        try:
            from telegram import Bot
            self._bot = Bot(token=config.token)
        except ImportError:
            raise IntegrationError(
                "python-telegram-bot package not installed. "
                "Install with: pip install flowagent[messaging]"
            )

    async def send(self, message: Message) -> bool:
        """Send a message to Telegram."""
        try:
            chat_id = message.channel or self.config.channel

            kwargs = {
                "chat_id": chat_id,
                "text": message.content,
            }

            if message.attachments:
                # Send first attachment as photo/document
                att = message.attachments[0]
                if "url" in att:
                    if att.get("type") == "photo":
                        await self._bot.send_photo(chat_id=chat_id, photo=att["url"])
                    else:
                        await self._bot.send_document(chat_id=chat_id, document=att["url"])

            await self._bot.send_message(**kwargs)
            logger.info(f"Telegram message sent to {chat_id}")
            return True

        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False

    async def send_to_channel(
        self,
        channel: str,
        content: str,
        **kwargs,
    ) -> bool:
        """Send a message to a specific Telegram chat."""
        message = Message(content=content, channel=channel, **kwargs)
        return await self.send(message)


class Email(MessagingProvider):
    """
    Email messaging provider.

    Example:
        >>> email = Email(
        ...     smtp_host="smtp.gmail.com",
        ...     smtp_port=587,
        ...     username="...",
        ...     password="...",
        ... )
        >>> await email.send(Message(
        ...     content="Hello!",
        ...     subject="Test",
        ...     channel="user@example.com",
        ... ))
    """

    def __init__(self, config: Optional[MessagingConfig] = None, **kwargs):
        if config is None:
            config = MessagingConfig(**kwargs)
        super().__init__(config)

        self._smtp_host = kwargs.get("smtp_host", "smtp.gmail.com")
        self._smtp_port = kwargs.get("smtp_port", 587)
        self._username = kwargs.get("username", "")
        self._password = kwargs.get("password", "")
        self._from_email = kwargs.get("from_email", self._username)

    async def send(self, message: Message) -> bool:
        """Send an email."""
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = self._from_email
            msg["To"] = message.channel
            msg["Subject"] = message.subject or "Message from FlowAgent"

            msg.attach(MIMEText(message.content, "plain"))

            if message.attachments:
                for att in message.attachments:
                    if "path" in att:
                        with open(att["path"], "rb") as f:
                            part = MIMEText(f.read(), "base64", "utf-8")
                            part.add_header(
                                "Content-Disposition",
                                "attachment",
                                filename=att.get("filename", "attachment"),
                            )
                            msg.attach(part)

            await aiosmtplib.send(
                msg,
                hostname=self._smtp_host,
                port=self._smtp_port,
                username=self._username,
                password=self._password,
                use_tls=True,
            )

            logger.info(f"Email sent to {message.channel}")
            return True

        except ImportError:
            raise IntegrationError(
                "aiosmtplib package not installed. "
                "Install with: pip install aiosmtplib"
            )
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False

    async def send_to_channel(
        self,
        channel: str,
        content: str,
        subject: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """Send an email to a specific address."""
        message = Message(
            content=content,
            channel=channel,
            subject=subject,
            **kwargs,
        )
        return await self.send(message)


class Webhook(MessagingProvider):
    """
    Webhook messaging provider.

    Example:
        >>> webhook = Webhook(webhook_url="https://hooks.slack.com/...")
        >>> await webhook.send(Message(content="Hello!"))
    """

    def __init__(self, config: Optional[MessagingConfig] = None, **kwargs):
        if config is None:
            config = MessagingConfig(**kwargs)
        super().__init__(config)

        try:
            import httpx
            self._client = httpx.AsyncClient()
        except ImportError:
            raise IntegrationError(
                "httpx package not installed. "
                "Install with: pip install flowagent"
            )

    async def send(self, message: Message) -> bool:
        """Send a webhook."""
        try:
            url = self.config.webhook_url

            payload = {
                "text": message.content,
                "channel": message.channel,
                "username": self.config.username or "FlowAgent",
            }

            if self.config.icon_emoji:
                payload["icon_emoji"] = self.config.icon_emoji

            if message.attachments:
                payload["attachments"] = message.attachments

            response = await self._client.post(
                url,
                json=payload,
                timeout=30.0,
            )

            response.raise_for_status()
            logger.info(f"Webhook sent to {url}")
            return True

        except Exception as e:
            logger.error(f"Webhook send error: {e}")
            return False

    async def send_to_channel(
        self,
        channel: str,
        content: str,
        **kwargs,
    ) -> bool:
        """Send a webhook with custom channel."""
        message = Message(content=content, channel=channel, **kwargs)
        return await self.send(message)

    async def send_with_headers(
        self,
        url: str,
        content: str,
        headers: Dict[str, str],
        method: str = "POST",
    ) -> bool:
        """Send a webhook with custom headers and method."""
        try:
            response = await self._client.request(
                method,
                url,
                content=content,
                headers=headers,
                timeout=30.0,
            )

            response.raise_for_status()
            logger.info(f"Webhook sent to {url}")
            return True

        except Exception as e:
            logger.error(f"Webhook send error: {e}")
            return False
