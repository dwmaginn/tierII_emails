"""Test fixtures for TierII email system configuration testing.

This package contains configuration fixtures for different user setups:
- david_config: MailerSend configuration for David
- luke_config: MailerSend configuration for Luke

All fixtures are configured to use testdata.csv to prevent sending
unintended emails during testing."""

from .david_config import get_david_config, apply_david_config, clear_david_config
from .luke_config import get_luke_config, apply_luke_config, clear_luke_config

__all__ = [
    "get_david_config",
    "apply_david_config",
    "clear_david_config",
    "get_luke_config",
    "apply_luke_config",
    "clear_luke_config",
]
