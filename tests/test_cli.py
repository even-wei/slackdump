"""Tests for SlackDump CLI functionality."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from argparse import ArgumentParser

from slackdump.cli import parse_datetime, create_parser, print_preview, main


class TestParseDatetime:
    """Test datetime parsing functionality."""

    def test_parse_date_only(self):
        """Test parsing date-only format."""
        result = parse_datetime("2023-01-01")
        expected = datetime(2023, 1, 1)
        assert result == expected

    def test_parse_date_time_seconds(self):
        """Test parsing date with time including seconds."""
        result = parse_datetime("2023-01-01 12:30:45")
        expected = datetime(2023, 1, 1, 12, 30, 45)
        assert result == expected

    def test_parse_iso_format(self):
        """Test parsing ISO format."""
        result = parse_datetime("2023-01-01T12:30:45")
        expected = datetime(2023, 1, 1, 12, 30, 45)
        assert result == expected

    def test_parse_date_time_minutes(self):
        """Test parsing date with time without seconds."""
        result = parse_datetime("2023-01-01 12:30")
        expected = datetime(2023, 1, 1, 12, 30)
        assert result == expected

    def test_parse_invalid_format(self):
        """Test parsing invalid date format."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_datetime("invalid-date")

    def test_parse_partial_date(self):
        """Test parsing incomplete date."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_datetime("2023-01")

    def test_parse_invalid_date_values(self):
        """Test parsing with invalid date values."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_datetime("2023-13-01")  # Invalid month

        with pytest.raises(ValueError, match="Invalid date format"):
            parse_datetime("2023-01-32")  # Invalid day


class TestCreateParser:
    """Test argument parser creation."""

    def test_parser_creation(self):
        """Test that parser is created correctly."""
        parser = create_parser()
        assert isinstance(parser, ArgumentParser)
        assert parser.prog == "slackdump"

    def test_required_arguments(self):
        """Test required arguments are properly configured."""
        parser = create_parser()

        # Test with missing required arguments
        with pytest.raises(SystemExit):
            parser.parse_args([])

        # Test with both required arguments
        args = parser.parse_args(["--token", "xoxb-test", "--channel", "C123"])
        assert args.token == "xoxb-test"
        assert args.channel == "C123"

    def test_optional_arguments(self):
        """Test optional arguments parsing."""
        parser = create_parser()

        args = parser.parse_args(
            [
                "--token",
                "xoxb-test",
                "--channel",
                "C123",
                "--output",
                "test.json",
                "--format",
                "csv",
                "--limit",
                "100",
                "--start-time",
                "2023-01-01",
                "--end-time",
                "2023-12-31",
                "--regex",
                "hello",
                "--case-sensitive",
                "--users",
                "U123",
                "U456",
            ]
        )

        assert args.output == "test.json"
        assert args.format == "csv"
        assert args.limit == 100
        assert args.start_time == "2023-01-01"
        assert args.end_time == "2023-12-31"
        assert args.regex == "hello"
        assert args.case_sensitive is True
        assert args.users == ["U123", "U456"]

    def test_default_values(self):
        """Test default values for optional arguments."""
        parser = create_parser()
        args = parser.parse_args(["--token", "xoxb-test", "--channel", "C123"])

        assert args.output is None
        assert args.format == "json"
        assert args.limit is None
        assert args.start_time is None
        assert args.end_time is None
        assert args.regex is None
        assert args.case_sensitive is False
        assert args.users is None

    def test_format_choices(self):
        """Test format argument choices."""
        parser = create_parser()

        # Valid format
        args = parser.parse_args(
            ["--token", "xoxb-test", "--channel", "C123", "--format", "json"]
        )
        assert args.format == "json"

        args = parser.parse_args(
            ["--token", "xoxb-test", "--channel", "C123", "--format", "csv"]
        )
        assert args.format == "csv"

        # Invalid format should cause system exit
        with pytest.raises(SystemExit):
            parser.parse_args(
                ["--token", "xoxb-test", "--channel", "C123", "--format", "xml"]
            )


class TestPrintPreview:
    """Test preview printing functionality."""

    def test_print_preview_few_messages(self):
        """Test preview with less than 10 messages."""
        # Create mock messages
        messages = []
        for i in range(3):
            mock_msg = Mock()
            mock_msg.to_dict.return_value = {
                "datetime": f"2023-01-0{i+1}T12:00:00",
                "user": f"U{i}",
                "text": f"Message {i+1}",
            }
            messages.append(mock_msg)

        with patch("builtins.print") as mock_print:
            print_preview(messages, 3)

        # Verify print calls
        mock_print.assert_any_call("\n📋 Showing first 10 of 3 messages:\n")
        mock_print.assert_any_call(" 1. [2023-01-01T12:00:00] U0: Message 1")
        mock_print.assert_any_call(" 2. [2023-01-02T12:00:00] U1: Message 2")
        mock_print.assert_any_call(" 3. [2023-01-03T12:00:00] U2: Message 3")

    def test_print_preview_many_messages(self):
        """Test preview with more than 10 messages."""
        # Create mock messages
        messages = []
        for i in range(15):
            mock_msg = Mock()
            mock_msg.to_dict.return_value = {
                "datetime": f"2023-01-{i+1:02d}T12:00:00",
                "user": f"U{i}",
                "text": f"Message {i+1}",
            }
            messages.append(mock_msg)

        with patch("builtins.print") as mock_print:
            print_preview(messages[:10], 15)  # Only first 10 passed to function

        # Verify pagination hint is shown
        mock_print.assert_any_call(
            "\n💡 Use --output to save all 15 messages to a file"
        )

    def test_print_preview_long_message(self):
        """Test preview with long message text."""
        # Create mock message with long text
        long_text = (
            "This is a very long message that exceeds 100 characters and should be "
            "truncated in the preview display"
        )
        mock_msg = Mock()
        mock_msg.to_dict.return_value = {
            "datetime": "2023-01-01T12:00:00",
            "user": "U123",
            "text": long_text,
        }

        with patch("builtins.print") as mock_print:
            print_preview([mock_msg], 1)

        # Verify truncation indicator is shown
        mock_print.assert_any_call("    ...")


class TestMainFunction:
    """Test main CLI function."""

    @patch("slackdump.cli.SlackMessageParser")
    @patch("sys.argv", ["slackdump", "--token", "invalid-token", "--channel", "C123"])
    def test_main_invalid_token_format(self, mock_parser):
        """Test main with invalid token format."""
        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            mock_print.assert_any_call(
                "❌ Error: Invalid token format. Slack bot tokens should "
                "start with 'xoxb-'"
            )

    @patch("slackdump.cli.SlackMessageParser")
    @patch(
        "sys.argv",
        ["slackdump", "--token", "xoxb-test", "--channel", "invalid-channel"],
    )
    def test_main_invalid_channel_format(self, mock_parser):
        """Test main with invalid channel format."""
        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            mock_print.assert_any_call(
                "❌ Error: Invalid channel format. Channel IDs should start with 'C'"
            )

    @patch("slackdump.cli.SlackMessageParser")
    @patch("sys.argv", ["slackdump", "--token", "xoxb-test", "--channel", "C123"])
    def test_main_successful_execution(self, mock_parser_class):
        """Test successful main execution without output file."""
        # Mock parser instance and methods
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser

        # Mock messages
        mock_msg = Mock()
        mock_msg.to_dict.return_value = {
            "datetime": "2023-01-01T12:00:00",
            "user": "U123",
            "text": "Test message",
        }
        mock_parser.get_channel_messages.return_value = [mock_msg]
        mock_parser.filter_messages.return_value = [mock_msg]

        with patch("slackdump.cli.print_preview") as mock_preview:
            with patch("builtins.print"):
                main()

        # Verify parser was called correctly
        mock_parser_class.assert_called_once_with("xoxb-test")
        mock_parser.get_channel_messages.assert_called_once_with("C123", None)
        mock_preview.assert_called_once()

    @patch("slackdump.cli.SlackMessageParser")
    @patch(
        "sys.argv",
        [
            "slackdump",
            "--token",
            "xoxb-test",
            "--channel",
            "C123",
            "--output",
            "test.json",
        ],
    )
    def test_main_with_output_file(self, mock_parser_class):
        """Test main execution with output file."""
        # Mock parser instance and methods
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser

        # Mock messages
        mock_msg = Mock()
        mock_parser.get_channel_messages.return_value = [mock_msg]
        mock_parser.filter_messages.return_value = [mock_msg]

        with patch("builtins.print"):
            main()

        # Verify export was called
        mock_parser.export_messages.assert_called_once_with(
            [mock_msg], "test.json", "json"
        )

    @patch("slackdump.cli.SlackMessageParser")
    @patch(
        "sys.argv",
        ["slackdump", "--token", "xoxb-test", "--channel", "C123", "--regex", "hello"],
    )
    def test_main_with_regex_filter(self, mock_parser_class):
        """Test main execution with regex filter."""
        # Mock parser instance
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.get_channel_messages.return_value = [Mock()]
        mock_parser.filter_messages.return_value = [Mock()]

        with patch("slackdump.cli.print_preview"):
            with patch("builtins.print"):
                main()

        # Verify filter_messages was called with filters
        assert mock_parser.filter_messages.called
        filters_arg = mock_parser.filter_messages.call_args[0][1]
        assert len(filters_arg) > 0  # At least one filter was applied

    @patch("slackdump.cli.SlackMessageParser")
    @patch(
        "sys.argv",
        [
            "slackdump",
            "--token",
            "xoxb-test",
            "--channel",
            "C123",
            "--start-time",
            "invalid-date",
        ],
    )
    def test_main_with_invalid_date(self, mock_parser_class):
        """Test main execution with invalid date format."""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.get_channel_messages.return_value = [Mock()]

        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            # Should print error about invalid date format
            print_calls = [str(call) for call in mock_print.call_args_list]
            error_printed = any("Invalid date format" in call for call in print_calls)
            assert error_printed

    @patch("slackdump.cli.SlackMessageParser")
    @patch("sys.argv", ["slackdump", "--token", "xoxb-test", "--channel", "C123"])
    def test_main_no_messages_found(self, mock_parser_class):
        """Test main execution when no messages found."""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.get_channel_messages.return_value = []  # No messages

        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0  # Successful exit, just no messages
            mock_print.assert_any_call("⚠️  No messages found in channel")

    @patch("slackdump.cli.SlackMessageParser")
    @patch("sys.argv", ["slackdump", "--token", "xoxb-test", "--channel", "C123"])
    def test_main_keyboard_interrupt(self, mock_parser_class):
        """Test main execution with keyboard interrupt."""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.get_channel_messages.side_effect = KeyboardInterrupt()

        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            mock_print.assert_any_call("\n⚠️  Operation cancelled by user")

    @patch("slackdump.cli.SlackMessageParser")
    @patch("sys.argv", ["slackdump", "--token", "xoxb-test", "--channel", "C123"])
    def test_main_connection_error(self, mock_parser_class):
        """Test main execution with connection error."""
        mock_parser_class.side_effect = ConnectionError("Network error occurred")

        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            mock_print.assert_any_call("❌ Network Error: Network error occurred")

    @patch("slackdump.cli.SlackMessageParser")
    @patch("sys.argv", ["slackdump", "--token", "xoxb-test", "--channel", "C123"])
    def test_main_value_error(self, mock_parser_class):
        """Test main execution with configuration error."""
        mock_parser_class.side_effect = ValueError("Invalid token")

        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            mock_print.assert_any_call("❌ Configuration Error: Invalid token")
