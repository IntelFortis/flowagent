"""
Logger - Logging configuration for FlowAgent.

This module provides the logging setup for FlowAgent.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


# Create console for rich output
console = Console()


def setup_logger(
    name: str = "flowagent",
    level: int = logging.INFO,
    rich: bool = True,
    file: Optional[str] = None,
) -> logging.Logger:
    """
    Set up the FlowAgent logger.

    Args:
        name: Logger name
        level: Logging level
        rich: Whether to use rich formatting
        file: Optional file path for logging

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatters
    if rich:
        formatter = None  # RichHandler handles formatting
        handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler = logging.StreamHandler(sys.stdout)

    if formatter:
        handler.setFormatter(formatter)

    logger.addHandler(handler)

    # Add file handler if specified
    if file:
        file_handler = logging.FileHandler(file)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logger.addHandler(file_handler)

    return logger


# Create default logger
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger.

    Args:
        name: Logger name

    Returns:
        Child logger
    """
    return logging.getLogger(f"flowagent.{name}")
