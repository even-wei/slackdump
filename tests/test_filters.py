"""Tests for SlackDump filtering functionality."""

import pytest
from datetime import datetime

from slackdump.parser import SlackMessage
from slackdump.filters import (
    TimeRangeFilter,
    RegexFilter,
    AuthorFilter,
    SlackMessageFilter,
)


class TestSlackMessageFilter:
    """Test base SlackMessageFilter class."""

    def test_abstract_base_class(self):
        """Test that base filter class raises NotImplementedError."""
        filter_obj = SlackMessageFilter()
        msg = SlackMessage("test", "U123", 1672531200.0, "C123")

        with pytest.raises(NotImplementedError):
            filter_obj(msg)


class TestTimeRangeFilter:
    """Test TimeRangeFilter class."""

    def test_init_no_times(self):
        """Test initialization with no time bounds."""
        filter_obj = TimeRangeFilter()
        assert filter_obj.start_time is None
        assert filter_obj.end_time is None

    def test_init_start_time_only(self):
        """Test initialization with only start time."""
        start = datetime(2023, 1, 1)
        filter_obj = TimeRangeFilter(start_time=start)
        assert filter_obj.start_time == start
        assert filter_obj.end_time is None

    def test_init_end_time_only(self):
        """Test initialization with only end time."""
        end = datetime(2023, 12, 31)
        filter_obj = TimeRangeFilter(end_time=end)
        assert filter_obj.start_time is None
        assert filter_obj.end_time == end

    def test_init_both_times(self):
        """Test initialization with both start and end times."""
        start = datetime(2023, 1, 1)
        end = datetime(2023, 12, 31)
        filter_obj = TimeRangeFilter(start_time=start, end_time=end)
        assert filter_obj.start_time == start
        assert filter_obj.end_time == end

    def test_init_invalid_range(self):
        """Test initialization with invalid time range."""
        start = datetime(2023, 12, 31)
        end = datetime(2023, 1, 1)

        with pytest.raises(ValueError, match="start_time must be before end_time"):
            TimeRangeFilter(start_time=start, end_time=end)

    def test_filter_no_bounds(self):
        """Test filtering with no time bounds (should pass all)."""
        filter_obj = TimeRangeFilter()

        msg = SlackMessage("test", "U123", 1672531200.0, "C123")  # 2023-01-01
        assert filter_obj(msg) is True

    def test_filter_start_time_only(self):
        """Test filtering with only start time."""
        start = datetime(2023, 1, 15)  # Jan 15, 2023
        filter_obj = TimeRangeFilter(start_time=start)

        # Message before start time
        msg_before = SlackMessage("test", "U123", 1672531200.0, "C123")  # 2023-01-01
        assert filter_obj(msg_before) is False

        # Message after start time
        msg_after = SlackMessage("test", "U123", 1674777600.0, "C123")  # 2023-01-27
        assert filter_obj(msg_after) is True

        # Message exactly at start time
        msg_exact = SlackMessage(
            "test", "U123", 1673827200.0, "C123"
        )  # 2023-01-15 12:00:00
        assert filter_obj(msg_exact) is True

    def test_filter_end_time_only(self):
        """Test filtering with only end time."""
        end = datetime(2023, 1, 15)  # Jan 15, 2023
        filter_obj = TimeRangeFilter(end_time=end)

        # Message before end time
        msg_before = SlackMessage("test", "U123", 1672531200.0, "C123")  # 2023-01-01
        assert filter_obj(msg_before) is True

        # Message after end time
        msg_after = SlackMessage("test", "U123", 1674777600.0, "C123")  # 2023-01-27
        assert filter_obj(msg_after) is False

        # Message exactly at end time (start of day)
        msg_exact = SlackMessage(
            "test", "U123", 1673712000.0, "C123"
        )  # 2023-01-15 00:00:00
        assert filter_obj(msg_exact) is True

    def test_filter_both_times(self):
        """Test filtering with both start and end times."""
        start = datetime(2023, 1, 10)
        end = datetime(2023, 1, 20)
        filter_obj = TimeRangeFilter(start_time=start, end_time=end)

        # Message before range
        msg_before = SlackMessage("test", "U123", 1672531200.0, "C123")  # 2023-01-01
        assert filter_obj(msg_before) is False

        # Message in range
        msg_in_range = SlackMessage("test", "U123", 1673827200.0, "C123")  # 2023-01-15
        assert filter_obj(msg_in_range) is True

        # Message after range
        msg_after = SlackMessage("test", "U123", 1674777600.0, "C123")  # 2023-01-27
        assert filter_obj(msg_after) is False


class TestRegexFilter:
    """Test RegexFilter class."""

    def test_init_case_insensitive_default(self):
        """Test initialization with default case insensitive."""
        filter_obj = RegexFilter("hello")
        assert filter_obj.pattern == "hello"
        assert filter_obj.case_sensitive is False

    def test_init_case_sensitive(self):
        """Test initialization with case sensitive."""
        filter_obj = RegexFilter("Hello", case_sensitive=True)
        assert filter_obj.pattern == "Hello"
        assert filter_obj.case_sensitive is True

    def test_init_invalid_regex(self):
        """Test initialization with invalid regex pattern."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            RegexFilter("[invalid")

    def test_filter_case_insensitive(self):
        """Test case insensitive regex filtering."""
        filter_obj = RegexFilter("hello")

        # Matching cases
        msg_lower = SlackMessage("hello world", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_lower) is True

        msg_upper = SlackMessage("HELLO WORLD", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_upper) is True

        msg_mixed = SlackMessage("Hello World", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_mixed) is True

        # Non-matching case
        msg_no_match = SlackMessage("goodbye world", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_no_match) is False

    def test_filter_case_sensitive(self):
        """Test case sensitive regex filtering."""
        filter_obj = RegexFilter("Hello", case_sensitive=True)

        # Matching case
        msg_match = SlackMessage("Hello World", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_match) is True

        # Non-matching cases
        msg_lower = SlackMessage("hello world", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_lower) is False

        msg_upper = SlackMessage("HELLO WORLD", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_upper) is False

        msg_no_match = SlackMessage("goodbye world", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_no_match) is False

    def test_filter_complex_regex(self):
        """Test complex regex patterns."""
        # Test word boundaries
        filter_obj = RegexFilter(r"\berror\b")

        msg_match = SlackMessage("An error occurred", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_match) is True

        msg_no_match = SlackMessage("No errors here", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_no_match) is False

        msg_partial = SlackMessage("terrorism is bad", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_partial) is False

    def test_filter_multiple_patterns(self):
        """Test regex with multiple patterns (OR logic)."""
        filter_obj = RegexFilter(r"error|warning|fail")

        msg_error = SlackMessage("An error occurred", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_error) is True

        msg_warning = SlackMessage("Warning: something", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_warning) is True

        msg_fail = SlackMessage("Operation failed", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_fail) is True

        msg_no_match = SlackMessage("Everything is fine", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_no_match) is False


class TestAuthorFilter:
    """Test AuthorFilter class."""

    def test_init_single_user(self):
        """Test initialization with single user."""
        filter_obj = AuthorFilter(["U123"])
        assert filter_obj.user_ids == {"U123"}

    def test_init_multiple_users(self):
        """Test initialization with multiple users."""
        users = ["U123", "U456", "U789"]
        filter_obj = AuthorFilter(users)
        assert filter_obj.user_ids == {"U123", "U456", "U789"}

    def test_init_empty_users(self):
        """Test initialization with empty user list."""
        with pytest.raises(ValueError, match="user_ids cannot be empty"):
            AuthorFilter([])

    def test_filter_allowed_user(self):
        """Test filtering with allowed user."""
        filter_obj = AuthorFilter(["U123", "U456"])

        msg_allowed_1 = SlackMessage("hello", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_allowed_1) is True

        msg_allowed_2 = SlackMessage("world", "U456", 1672531200.0, "C123")
        assert filter_obj(msg_allowed_2) is True

    def test_filter_disallowed_user(self):
        """Test filtering with disallowed user."""
        filter_obj = AuthorFilter(["U123", "U456"])

        msg_disallowed = SlackMessage("hello", "U999", 1672531200.0, "C123")
        assert filter_obj(msg_disallowed) is False

    def test_filter_duplicate_users_in_init(self):
        """Test that duplicate users in init are handled correctly."""
        filter_obj = AuthorFilter(["U123", "U456", "U123", "U456"])
        assert filter_obj.user_ids == {"U123", "U456"}

        msg_allowed = SlackMessage("hello", "U123", 1672531200.0, "C123")
        assert filter_obj(msg_allowed) is True


class TestFilterCombinations:
    """Test combinations of different filters."""

    def test_multiple_filters_all_pass(self):
        """Test message that passes all filters."""
        # Create filters
        time_filter = TimeRangeFilter(
            start_time=datetime(2023, 1, 1), end_time=datetime(2023, 12, 31)
        )
        regex_filter = RegexFilter("hello")
        author_filter = AuthorFilter(["U123"])

        # Message that should pass all filters
        msg = SlackMessage("hello world", "U123", 1672531200.0, "C123")  # 2023-01-01

        assert time_filter(msg) is True
        assert regex_filter(msg) is True
        assert author_filter(msg) is True

    def test_multiple_filters_one_fails(self):
        """Test message that fails one filter."""
        # Create filters
        time_filter = TimeRangeFilter(
            start_time=datetime(2023, 6, 1), end_time=datetime(2023, 12, 31)  # June 1st
        )
        regex_filter = RegexFilter("hello")
        author_filter = AuthorFilter(["U123"])

        # Message that should fail time filter (January 1st)
        msg = SlackMessage("hello world", "U123", 1672531200.0, "C123")

        assert time_filter(msg) is False  # Fails time filter
        assert regex_filter(msg) is True
        assert author_filter(msg) is True

    def test_edge_case_empty_message_text(self):
        """Test filters with empty message text."""
        regex_filter = RegexFilter("hello")

        msg_empty = SlackMessage("", "U123", 1672531200.0, "C123")
        assert regex_filter(msg_empty) is False

    def test_edge_case_special_characters_regex(self):
        """Test regex filter with special characters in message."""
        regex_filter = RegexFilter(r"\$\d+\.\d{2}")  # Match currency format

        msg_match = SlackMessage("The price is $19.99", "U123", 1672531200.0, "C123")
        assert regex_filter(msg_match) is True

        msg_no_match = SlackMessage("The price is 19.99", "U123", 1672531200.0, "C123")
        assert regex_filter(msg_no_match) is False
