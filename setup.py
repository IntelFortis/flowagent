"""
FlowAgent Setup Script

This is a compatibility setup script for older pip versions.
Modern pip will use pyproject.toml instead.
"""

from setuptools import setup, find_packages

setup(
    name="flowagent",
    version="0.1.0",
    author="IntelFortis",
    description="A small personal workflow automation experiment with a visual editor",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/IntelFortis/flowagent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.24.0",
        "anyio>=3.7.0",
        "tenacity>=8.2.0",
        "rich>=13.0.0",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "llm": [
            "openai>=1.0.0",
            "anthropic>=0.18.0",
            "google-generativeai>=0.3.0",
            "mistralai>=0.1.0",
        ],
        "database": [
            "sqlalchemy>=2.0.0",
            "asyncpg>=0.28.0",
            "pymongo>=4.4.0",
            "redis>=5.0.0",
            "elasticsearch>=8.10.0",
        ],
        "cloud": [
            "boto3>=1.28.0",
            "google-cloud-storage>=2.10.0",
            "azure-storage-blob>=12.17.0",
        ],
        "messaging": [
            "slack-sdk>=3.21.0",
            "discord.py>=2.3.0",
            "python-telegram-bot>=20.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "mypy>=1.5.0",
            "ruff>=0.1.0",
            "pre-commit>=3.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "flowagent=flowagent.cli:main",
        ],
    },
)
