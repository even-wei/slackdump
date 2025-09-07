"""Core Slack API interaction and message parsing functionality."""

import csv
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from .filters import SlackMessageFilter


class SlackMessage:
    """Data class representing a Slack message."""

    def __init__(
        self,
        text: str,
        user: str,
        timestamp: float,
        channel: str,
        thread_ts: Optional[str] = None,
        reply_count: int = 0,
        reactions: Optional[List[Dict]] = None,
    ):
        self.text = text
        self.user = user
        self.timestamp = timestamp
        self.channel = channel
        self.thread_ts = thread_ts
        self.reply_count = reply_count
        self.reactions = reactions or []

    @property
    def datetime(self) -> datetime:
        """Convert timestamp to datetime object."""
        return datetime.fromtimestamp(self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for export."""
        return {
            "text": self.text,
            "user": self.user,
            "timestamp": self.timestamp,
            "datetime": self.datetime.isoformat(),
            "channel": self.channel,
            "thread_ts": self.thread_ts,
            "reply_count": self.reply_count,
            "reactions": self.reactions,
        }


class SlackMessageParser:
    """Main class for interacting with Slack API."""

    def __init__(self, token: str):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )

        if not self._verify_token():
            raise ValueError(
                "Invalid Slack token. Please check your token format (xoxb-...)"
            )

    def _verify_token(self) -> bool:
        """Validate Slack token."""
        if not self.token.startswith("xoxb-"):
            return False

        try:
            response = self._make_request("auth.test", {})
            return bool(response.get("ok", False))
        except Exception:
            return False

    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """HTTP requests with rate limiting."""
        url = f"https://slack.com/api/{endpoint}"

        while True:
            try:
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    print(f"⏳ Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()
                data = response.json()

                if not data.get("ok", False):
                    error_msg = data.get("error", "Unknown error")
                    if error_msg == "channel_not_found":
                        raise ValueError(
                            "Channel not found. Please check the channel ID "
                            "format (C...)"
                        )
                    elif error_msg == "invalid_auth":
                        raise ValueError(
                            "Invalid authentication. Please check your token."
                        )
                    else:
                        raise ValueError(f"Slack API error: {error_msg}")

                return dict(data)

            except requests.exceptions.RequestException as e:
                raise ConnectionError(
                    f"Network error: {e}. Please check your connection and try again."
                )

    def get_channel_messages(
        self, channel_id: str, limit: Optional[int] = None
    ) -> List[SlackMessage]:
        """Fetch messages with pagination."""
        messages = []
        cursor = None
        fetched_count = 0

        while True:
            params = {
                "channel": channel_id,
                "limit": min(1000, limit - fetched_count) if limit else 1000,
            }

            if cursor:
                params["cursor"] = cursor

            print(f"📥 Fetching messages... ({fetched_count} so far)")

            try:
                data = self._make_request("conversations.history", params)
            except Exception as e:
                print(f"❌ Error fetching messages: {e}")
                raise

            batch_messages = data.get("messages", [])

            for msg_data in batch_messages:
                message = SlackMessage(
                    text=msg_data.get("text", ""),
                    user=msg_data.get("user", ""),
                    timestamp=float(msg_data.get("ts", 0)),
                    channel=channel_id,
                    thread_ts=msg_data.get("thread_ts"),
                    reply_count=int(msg_data.get("reply_count", 0)),
                    reactions=msg_data.get("reactions", []),
                )
                messages.append(message)

            fetched_count += len(batch_messages)

            if limit and fetched_count >= limit:
                messages = messages[:limit]
                break

            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        print(f"✅ Fetched {len(messages)} messages")
        return messages

    def filter_messages(
        self, messages: List[SlackMessage], filters: List["SlackMessageFilter"]
    ) -> List[SlackMessage]:
        """Apply filters to messages."""
        filtered_messages = messages

        for filter_obj in filters:
            filtered_messages = [msg for msg in filtered_messages if filter_obj(msg)]

        return filtered_messages

    def export_messages(
        self, messages: List[SlackMessage], output_path: str, format: str = "json"
    ) -> None:
        """Export messages to file."""
        if not messages:
            print("⚠️ No messages to export")
            return

        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        except (OSError, ValueError):
            pass

        try:
            if format.lower() == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(
                        [msg.to_dict() for msg in messages],
                        f,
                        indent=2,
                        ensure_ascii=False,
                    )

            elif format.lower() == "csv":
                with open(output_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [
                            "datetime",
                            "user",
                            "text",
                            "channel",
                            "thread_ts",
                            "reply_count",
                        ]
                    )

                    for msg in messages:
                        writer.writerow(
                            [
                                msg.datetime.isoformat(),
                                msg.user,
                                msg.text,
                                msg.channel,
                                msg.thread_ts or "",
                                msg.reply_count,
                            ]
                        )
            else:
                raise ValueError(f"Unsupported format: {format}. Use 'json' or 'csv'")

            print(f"📄 Exported {len(messages)} messages to {output_path}")

        except PermissionError:
            raise PermissionError(
                f"Permission denied writing to {output_path}. "
                "Please check file permissions."
            )
        except Exception as e:
            raise IOError(f"Error writing file: {e}")
