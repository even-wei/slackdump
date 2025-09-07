"""SlackDump - Fast Slack message dumping and filtering tool."""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .parser import SlackMessageParser, SlackMessage
from .filters import TimeRangeFilter, RegexFilter, AuthorFilter, SlackMessageFilter

__all__ = [
    "SlackMessageParser",
    "SlackMessage",
    "TimeRangeFilter",
    "RegexFilter",
    "AuthorFilter",
    "SlackMessageFilter",
]
