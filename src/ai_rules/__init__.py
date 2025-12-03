"""AI Rules - Manage AI agent configurations through symlinks."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ai-agent-rules")
except PackageNotFoundError:
    __version__ = "dev"
