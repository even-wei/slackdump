"""Message filtering classes for SlackDump."""

import re
from datetime import datetime
from typing import List, Optional, Set

from .parser import SlackMessage


class SlackMessageFilter:
    """Base class for message filters."""

    def __call__(self, message: SlackMessage) -> bool:
        """Return True if message should be included."""
        raise NotImplementedError("Subclasses must implement __call__")


class TimeRangeFilter(SlackMessageFilter):
    """Filter messages by date/time range."""

    def __init__(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ):
        self.start_time = start_time
        self.end_time = end_time

        if start_time and end_time and start_time > end_time:
            raise ValueError("start_time must be before end_time")

    def __call__(self, message: SlackMessage) -> bool:
        """Check if message timestamp falls within the specified range."""
        msg_datetime = message.datetime

        if self.start_time and msg_datetime < self.start_time:
            return False

        if self.end_time and msg_datetime > self.end_time:
            return False

        return True


class RegexFilter(SlackMessageFilter):
    """Filter messages by regex pattern."""

    def __init__(self, pattern: str, case_sensitive: bool = False):
        self.pattern = pattern
        self.case_sensitive = case_sensitive

        flags = 0 if case_sensitive else re.IGNORECASE

        try:
            self.regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{pattern}': {e}")

    def __call__(self, message: SlackMessage) -> bool:
        """Check if message text matches the regex pattern."""
        return bool(self.regex.search(message.text))


class AuthorFilter(SlackMessageFilter):
    """Filter messages by user IDs."""

    def __init__(self, user_ids: List[str]):
        if not user_ids:
            raise ValueError("user_ids cannot be empty")

        self.user_ids: Set[str] = set(user_ids)

    def __call__(self, message: SlackMessage) -> bool:
        """Check if message author is in the allowed user set."""
        return message.user in self.user_ids
