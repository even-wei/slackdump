"""CLI argument parsing and main logic for SlackDump."""

import argparse
from argparse import Namespace
import sys
from datetime import datetime
from typing import Any, List

from .filters import AuthorFilter, RegexFilter, SlackMessageFilter, TimeRangeFilter
from .parser import SlackMessageParser


def parse_datetime(date_str: str) -> datetime:
    """Parse datetime string in multiple formats."""
    formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(
        f"Invalid date format: {date_str}. "
        f"Supported formats: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, "
        f"YYYY-MM-DDTHH:MM:SS, YYYY-MM-DD HH:MM"
    )


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="slackdump",
        description="Fast, powerful CLI tool for dumping and filtering Slack messages",
        epilog="""
Examples:
  slackdump --token xoxb-... --channel C1234567890
  slackdump --token xoxb-... --channel C1234567890 --output messages.json
  slackdump --token xoxb-... --channel C1234567890 --limit 100 --format csv
  slackdump --token xoxb-... --channel C1234567890 --regex "error|warning" \\
      --case-sensitive
  slackdump --token xoxb-... --channel C1234567890 --start-time "2023-01-01" \\
      --end-time "2023-12-31"
  slackdump --token xoxb-... --channel C1234567890 --users U1234567890 U0987654321
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Required arguments
    required = parser.add_argument_group("required arguments")
    required.add_argument("--token", required=True, help="Slack Bot Token (xoxb-...)")
    required.add_argument("--channel", required=True, help="Channel ID (C...)")

    # Optional arguments
    parser.add_argument("--output", help="Output file path")
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument("--limit", type=int, help="Max messages to fetch")
    parser.add_argument(
        "--start-time", help="Start time filter (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"
    )
    parser.add_argument(
        "--end-time", help="End time filter (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"
    )
    parser.add_argument("--regex", help="Regex pattern filter")
    parser.add_argument(
        "--case-sensitive", action="store_true", help="Case sensitive regex"
    )
    parser.add_argument("--users", nargs="+", help="Filter by user IDs")
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    return parser


def print_preview(messages: List[Any], total_count: int) -> None:
    """Print first 10 messages to stdout with pagination hint."""
    print(f"\n📋 Showing first 10 of {total_count} messages:\n")

    for i, msg in enumerate(messages[:10], 1):
        msg_dict = msg.to_dict()
        datetime_str = msg_dict["datetime"][:19]
        user = msg_dict["user"]
        text = msg_dict["text"][:100]
        print(f"{i:2d}. [{datetime_str}] {user}: {text}")
        if len(msg_dict["text"]) > 100:
            print("    ...")

    if total_count > 10:
        print(f"\n💡 Use --output to save all {total_count} messages to a file")


def validate_inputs(args: Namespace) -> None:
    """Validate token and channel format."""
    if not args.token.startswith("xoxb-"):
        print(
            "❌ Error: Invalid token format. Slack bot tokens should start with 'xoxb-'"
        )
        print("💡 Setup instructions:")
        print("   1. Go to https://api.slack.com/apps")
        print("   2. Create a new app or select existing app")
        print("   3. Go to OAuth & Permissions")
        print("   4. Add 'channels:history' scope")
        print("   5. Install app to workspace")
        print("   6. Copy 'Bot User OAuth Token' (starts with xoxb-)")
        sys.exit(1)

    if not args.channel.startswith("C"):
        print("❌ Error: Invalid channel format. Channel IDs should start with 'C'")
        print("💡 To find channel ID:")
        print("   1. Right-click on channel name in Slack")
        print("   2. Select 'Copy link'")
        print("   3. Extract ID from URL (e.g., C1234567890)")
        sys.exit(1)


def create_filters(args: Namespace) -> List[SlackMessageFilter]:
    """Create message filters based on arguments."""
    filters: List[SlackMessageFilter] = []

    # Time range filter
    if args.start_time or args.end_time:
        try:
            start_time = (
                parse_datetime(args.start_time) if args.start_time else None
            )
            end_time = parse_datetime(args.end_time) if args.end_time else None
            filters.append(TimeRangeFilter(start_time, end_time))
            start_str = args.start_time or "start"
            end_str = args.end_time or "end"
            print(f"🕒 Applied time filter: {start_str} to {end_str}")
        except ValueError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    # Regex filter
    if args.regex:
        try:
            filters.append(RegexFilter(args.regex, args.case_sensitive))
            case_info = (
                " (case-sensitive)" if args.case_sensitive else " (case-insensitive)"
            )
            print(f"🔍 Applied regex filter: '{args.regex}'{case_info}")
        except ValueError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    # Author filter
    if args.users:
        filters.append(AuthorFilter(args.users))
        print(f"👥 Applied user filter: {', '.join(args.users)}")

    return filters


def process_messages(args: Namespace) -> None:
    """Process and filter messages."""
    # Initialize parser
    print("🔧 Initializing Slack API connection...")
    slack_parser = SlackMessageParser(args.token)

    # Fetch messages
    print(f"📡 Fetching messages from channel {args.channel}...")
    messages = slack_parser.get_channel_messages(args.channel, args.limit)

    if not messages:
        print("⚠️  No messages found in channel")
        sys.exit(0)

    # Apply filters
    filters = create_filters(args)
    if filters:
        original_count = len(messages)
        messages = slack_parser.filter_messages(messages, filters)
        print(f"✅ Filtered {original_count} → {len(messages)} messages")

    # Handle output
    if args.output:
        try:
            slack_parser.export_messages(messages, args.output, args.format)
        except (PermissionError, IOError) as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    else:
        print_preview(messages, len(messages))


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    validate_inputs(args)

    try:
        process_messages(args)
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)
    except ConnectionError as e:
        print(f"❌ Network Error: {e}")
        print(
            "💡 Try again in a few moments. If problem persists, "
            "check your internet connection."
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print(
            "💡 Please check your inputs and try again. If problem persists, "
            "please report this issue."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
