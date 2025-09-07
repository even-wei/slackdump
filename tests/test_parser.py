"""Tests for SlackDump parser functionality."""

import json
import pytest
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

from slackdump.parser import SlackMessage, SlackMessageParser


class TestSlackMessage:
    """Test SlackMessage class."""

    def test_init(self):
        """Test SlackMessage initialization."""
        msg = SlackMessage(
            text="Hello world!",
            user="U1234567890",
            timestamp=1672531200.123456,
            channel="C1234567890",
        )

        assert msg.text == "Hello world!"
        assert msg.user == "U1234567890"
        assert msg.timestamp == 1672531200.123456
        assert msg.channel == "C1234567890"
        assert msg.thread_ts is None
        assert msg.reply_count == 0
        assert msg.reactions == []

    def test_init_with_optional_fields(self):
        """Test SlackMessage initialization with optional fields."""
        reactions = [{"name": "thumbsup", "count": 1}]
        msg = SlackMessage(
            text="Hello world!",
            user="U1234567890",
            timestamp=1672531200.123456,
            channel="C1234567890",
            thread_ts="1672531199.123456",
            reply_count=5,
            reactions=reactions,
        )

        assert msg.thread_ts == "1672531199.123456"
        assert msg.reply_count == 5
        assert msg.reactions == reactions

    def test_datetime_property(self):
        """Test datetime property conversion."""
        msg = SlackMessage(
            text="Hello world!",
            user="U1234567890",
            timestamp=1672531200.0,
            channel="C1234567890",
        )

        expected_dt = datetime.fromtimestamp(1672531200.0)
        assert msg.datetime == expected_dt

    def test_to_dict(self):
        """Test to_dict serialization."""
        reactions = [{"name": "thumbsup", "count": 1}]
        msg = SlackMessage(
            text="Hello world!",
            user="U1234567890",
            timestamp=1672531200.123456,
            channel="C1234567890",
            thread_ts="1672531199.123456",
            reply_count=5,
            reactions=reactions,
        )

        result = msg.to_dict()
        expected_dt = datetime.fromtimestamp(1672531200.123456)

        assert result == {
            "text": "Hello world!",
            "user": "U1234567890",
            "timestamp": 1672531200.123456,
            "datetime": expected_dt.isoformat(),
            "channel": "C1234567890",
            "thread_ts": "1672531199.123456",
            "reply_count": 5,
            "reactions": reactions,
        }


class TestSlackMessageParser:
    """Test SlackMessageParser class."""

    @patch("slackdump.parser.requests.Session")
    def test_init_valid_token(self, mock_session_class):
        """Test parser initialization with valid token."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock successful auth.test response
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True}
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response

        parser = SlackMessageParser("xoxb-valid-token")

        assert parser.token == "xoxb-valid-token"
        mock_session.headers.update.assert_called_once_with(
            {
                "Authorization": "Bearer xoxb-valid-token",
                "Content-Type": "application/json",
            }
        )

    @patch("slackdump.parser.requests.Session")
    def test_init_invalid_token_format(self, mock_session_class):
        """Test parser initialization with invalid token format."""
        with pytest.raises(ValueError, match="Invalid Slack token"):
            SlackMessageParser("invalid-token")

    @patch("slackdump.parser.requests.Session")
    def test_init_invalid_token_auth_fail(self, mock_session_class):
        """Test parser initialization with token that fails auth."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock failed auth.test response
        mock_response = Mock()
        mock_response.json.return_value = {"ok": False}
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response

        with pytest.raises(ValueError, match="Invalid Slack token"):
            SlackMessageParser("xoxb-invalid-token")

    @patch("slackdump.parser.requests.Session")
    def test_verify_token_success(self, mock_session_class):
        """Test successful token verification."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.json.return_value = {"ok": True}
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response

        parser = SlackMessageParser("xoxb-valid-token")
        assert parser._verify_token() is True

    @patch("slackdump.parser.requests.Session")
    def test_make_request_success(self, mock_session_class):
        """Test successful API request."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock auth.test for initialization
        mock_auth_response = Mock()
        mock_auth_response.json.return_value = {"ok": True}
        mock_auth_response.status_code = 200

        # Mock actual request
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "data": "test"}
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None

        mock_session.get.side_effect = [mock_auth_response, mock_response]

        parser = SlackMessageParser("xoxb-valid-token")
        result = parser._make_request("test.endpoint", {"param": "value"})

        assert result == {"ok": True, "data": "test"}

    @patch("slackdump.parser.requests.Session")
    def test_make_request_rate_limit(self, mock_session_class):
        """Test API request with rate limiting."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock auth.test for initialization
        mock_auth_response = Mock()
        mock_auth_response.json.return_value = {"ok": True}
        mock_auth_response.status_code = 200

        # Mock rate limited response, then success
        mock_rate_limit_response = Mock()
        mock_rate_limit_response.status_code = 429
        mock_rate_limit_response.headers = {"Retry-After": "1"}

        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"ok": True, "data": "test"}
        mock_success_response.raise_for_status.return_value = None

        mock_session.get.side_effect = [
            mock_auth_response,
            mock_rate_limit_response,
            mock_success_response,
        ]

        with patch("time.sleep"):  # Mock sleep to speed up test
            parser = SlackMessageParser("xoxb-valid-token")
            result = parser._make_request("test.endpoint", {"param": "value"})

        assert result == {"ok": True, "data": "test"}

    @patch("slackdump.parser.requests.Session")
    def test_make_request_api_error(self, mock_session_class):
        """Test API request with Slack API error."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock auth.test for initialization
        mock_auth_response = Mock()
        mock_auth_response.json.return_value = {"ok": True}
        mock_auth_response.status_code = 200

        # Mock API error response
        mock_error_response = Mock()
        mock_error_response.status_code = 200
        mock_error_response.json.return_value = {
            "ok": False,
            "error": "channel_not_found",
        }
        mock_error_response.raise_for_status.return_value = None

        mock_session.get.side_effect = [mock_auth_response, mock_error_response]

        parser = SlackMessageParser("xoxb-valid-token")

        with pytest.raises(ValueError, match="Channel not found"):
            parser._make_request("test.endpoint", {"param": "value"})

    @patch("slackdump.parser.requests.Session")
    def test_get_channel_messages(self, mock_session_class):
        """Test fetching channel messages."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock auth.test for initialization
        mock_auth_response = Mock()
        mock_auth_response.json.return_value = {"ok": True}
        mock_auth_response.status_code = 200

        # Mock messages response
        mock_messages_response = Mock()
        mock_messages_response.status_code = 200
        mock_messages_response.json.return_value = {
            "ok": True,
            "messages": [
                {
                    "text": "Hello world!",
                    "user": "U1234567890",
                    "ts": "1672531200.123456",
                    "reactions": [],
                },
                {
                    "text": "Second message",
                    "user": "U0987654321",
                    "ts": "1672531300.123456",
                    "thread_ts": "1672531200.123456",
                    "reply_count": 2,
                    "reactions": [{"name": "thumbsup", "count": 1}],
                },
            ],
        }
        mock_messages_response.raise_for_status.return_value = None

        mock_session.get.side_effect = [mock_auth_response, mock_messages_response]

        parser = SlackMessageParser("xoxb-valid-token")
        messages = parser.get_channel_messages("C1234567890")

        assert len(messages) == 2

        msg1 = messages[0]
        assert msg1.text == "Hello world!"
        assert msg1.user == "U1234567890"
        assert msg1.timestamp == 1672531200.123456
        assert msg1.channel == "C1234567890"
        assert msg1.thread_ts is None
        assert msg1.reply_count == 0
        assert msg1.reactions == []

        msg2 = messages[1]
        assert msg2.text == "Second message"
        assert msg2.user == "U0987654321"
        assert msg2.timestamp == 1672531300.123456
        assert msg2.thread_ts == "1672531200.123456"
        assert msg2.reply_count == 2
        assert msg2.reactions == [{"name": "thumbsup", "count": 1}]

    @patch("slackdump.parser.requests.Session")
    def test_export_messages_json(self, mock_session_class):
        """Test exporting messages to JSON."""
        # Setup parser with mocked session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_auth_response = Mock()
        mock_auth_response.json.return_value = {"ok": True}
        mock_auth_response.status_code = 200
        mock_session.get.return_value = mock_auth_response

        parser = SlackMessageParser("xoxb-valid-token")

        # Create test messages
        messages = [
            SlackMessage("Hello", "U123", 1672531200.0, "C123"),
            SlackMessage("World", "U456", 1672531300.0, "C123"),
        ]

        # Mock file operations
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            with patch("os.makedirs"):
                parser.export_messages(messages, "test.json", "json")

        # Verify file was opened correctly
        mock_file.assert_called_once_with("test.json", "w", encoding="utf-8")

        # Verify JSON was written (check if json.dump was called with correct data)
        written_data = mock_file().write.call_args_list
        written_content = "".join(call[0][0] for call in written_data)
        parsed_data = json.loads(written_content)

        assert len(parsed_data) == 2
        assert parsed_data[0]["text"] == "Hello"
        assert parsed_data[1]["text"] == "World"

    @patch("slackdump.parser.requests.Session")
    def test_export_messages_csv(self, mock_session_class):
        """Test exporting messages to CSV."""
        # Setup parser with mocked session
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_auth_response = Mock()
        mock_auth_response.json.return_value = {"ok": True}
        mock_auth_response.status_code = 200
        mock_session.get.return_value = mock_auth_response

        parser = SlackMessageParser("xoxb-valid-token")

        # Create test messages
        messages = [
            SlackMessage("Hello", "U123", 1672531200.0, "C123"),
            SlackMessage("World", "U456", 1672531300.0, "C123"),
        ]

        # Mock file operations
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            with patch("os.makedirs"):
                parser.export_messages(messages, "test.csv", "csv")

        # Verify file was opened correctly
        mock_file.assert_called_once_with("test.csv", "w", newline="", encoding="utf-8")

        # Verify CSV header and data were written
        handle = mock_file()
        write_calls = [call[0][0] for call in handle.write.call_args_list]

        # Should contain CSV header and data rows
        csv_content = "".join(write_calls)
        assert "datetime,user,text,channel,thread_ts,reply_count" in csv_content
        assert "Hello" in csv_content
        assert "World" in csv_content

    @patch("slackdump.parser.requests.Session")
    def test_filter_messages(self, mock_session_class):
        """Test message filtering."""
        # Setup parser
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_auth_response = Mock()
        mock_auth_response.json.return_value = {"ok": True}
        mock_auth_response.status_code = 200
        mock_session.get.return_value = mock_auth_response

        parser = SlackMessageParser("xoxb-valid-token")

        # Create test messages
        messages = [
            SlackMessage("Hello world", "U123", 1672531200.0, "C123"),
            SlackMessage("Goodbye", "U456", 1672531300.0, "C123"),
            SlackMessage("Hello again", "U123", 1672531400.0, "C123"),
        ]

        # Create mock filter that only allows messages containing "Hello"
        mock_filter = Mock()
        mock_filter.side_effect = lambda msg: "Hello" in msg.text

        filtered = parser.filter_messages(messages, [mock_filter])

        assert len(filtered) == 2
        assert filtered[0].text == "Hello world"
        assert filtered[1].text == "Hello again"
