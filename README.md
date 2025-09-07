# SlackDump

[![PyPI version](https://badge.fury.io/py/slackdump.svg)](https://badge.fury.io/py/slackdump)
[![Tests](https://github.com/yourusername/slackdump/workflows/Test/badge.svg)](https://github.com/yourusername/slackdump/actions)
[![Coverage](https://codecov.io/gh/yourusername/slackdump/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/slackdump)
[![Python Versions](https://img.shields.io/pypi/pyversions/slackdump.svg)](https://pypi.org/project/slackdump/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A fast, powerful CLI tool for dumping and filtering Slack messages. Built with modern Python tooling using [uv](https://docs.astral.sh/uv/).

## ✨ Features

- 🚀 **Fast & Efficient**: Handle large channels (10k+ messages) with automatic pagination
- 🔍 **Advanced Filtering**: Time-based, regex, and user-based filtering
- 📊 **Multiple Formats**: Export to JSON or CSV
- 🛡️ **Rate Limiting**: Automatic handling of Slack API rate limits
- 🎯 **User-Friendly**: Intuitive CLI with helpful error messages
- 🔧 **Reliable**: Comprehensive error handling and recovery

## 🚀 Quick Start

### Installation

```bash
# Using uv (recommended)
uv add slackdump

# Using pip
pip install slackdump
```

### Basic Usage

```bash
# Dump all messages from a channel
slackdump --token xoxb-your-token --channel C1234567890

# Export to file
slackdump --token xoxb-your-token --channel C1234567890 --output messages.json

# Limit number of messages
slackdump --token xoxb-your-token --channel C1234567890 --limit 100
```

## 📋 Setup Instructions

### 1. Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Choose your app name and workspace

### 2. Configure Permissions

1. Go to "OAuth & Permissions" in your app settings
2. Add the following scopes under "Bot Token Scopes":
   - `channels:history` - View messages and content in public channels
   - `channels:read` - View basic information about public channels

### 3. Install App

1. Click "Install to Workspace"
2. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 4. Find Channel ID

1. Right-click on the channel name in Slack
2. Select "Copy link"
3. Extract the channel ID from the URL (e.g., `C1234567890`)

## 📖 Usage Examples

### Time-Based Filtering

```bash
# Messages from a specific date
slackdump --token xoxb-... --channel C123... --start-time "2023-01-01" --end-time "2023-12-31"

# Messages from last week
slackdump --token xoxb-... --channel C123... --start-time "2023-12-01 09:00:00"
```

### Content Filtering

```bash
# Filter by regex pattern
slackdump --token xoxb-... --channel C123... --regex "error|warning|fail"

# Case-sensitive search
slackdump --token xoxb-... --channel C123... --regex "Error" --case-sensitive
```

### User Filtering

```bash
# Messages from specific users
slackdump --token xoxb-... --channel C123... --users U1234567890 U0987654321
```

### Export Formats

```bash
# Export as JSON (default)
slackdump --token xoxb-... --channel C123... --output messages.json

# Export as CSV
slackdump --token xoxb-... --channel C123... --output messages.csv --format csv
```

### Combined Filters

```bash
# Complex filtering example
slackdump --token xoxb-... --channel C123... \\
  --start-time "2023-01-01" \\
  --end-time "2023-01-31" \\
  --regex "important|urgent" \\
  --users U1234567890 \\
  --output important_messages.json
```

## 🐍 Programmatic Usage

```python
from slackdump import SlackMessageParser, TimeRangeFilter, RegexFilter
from datetime import datetime

# Initialize parser
parser = SlackMessageParser('xoxb-your-token')

# Fetch messages
messages = parser.get_channel_messages('C1234567890', limit=100)

# Apply filters
filters = [
    TimeRangeFilter(
        start_time=datetime(2023, 1, 1),
        end_time=datetime(2023, 12, 31)
    ),
    RegexFilter('error|warning', case_sensitive=False)
]
filtered_messages = parser.filter_messages(messages, filters)

# Export
parser.export_messages(filtered_messages, 'output.json', 'json')
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/slackdump.git
cd slackdump

# Quick setup using Makefile (recommended)
make dev-setup

# Or manual setup
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies (automatically creates virtual environment)
uv sync --all-extras
```

### Using the Makefile

The project includes a comprehensive Makefile for streamlined development:

```bash
# Quick start
make help          # Show all available commands
make dev-setup     # Set up development environment
make test          # Run tests
make pre-commit    # Run all quality checks

# Development workflow
make format        # Format code with black
make lint          # Run linter (flake8)
make type-check    # Run type checker (mypy)
make coverage      # Run tests with coverage report

# Build and publish
make build         # Build package for distribution
make publish       # Publish to PyPI (with confirmation)

# Utilities
make demo          # Show CLI demo
make clean         # Clean cache and build files
make show-env      # Show environment information
```

### Manual Commands (without Makefile)

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=slackdump

# Run specific test file
uv run pytest tests/test_parser.py
```

### Code Quality

```bash
# Using Makefile (recommended)
make format        # Format code
make lint          # Lint code
make type-check    # Type checking
make check-all     # Run all quality checks

# Manual commands
uv run black .     # Format code
uv run flake8 .    # Lint code
uv run mypy slackdump  # Type checking
```

## 📝 Command Reference

```
slackdump --token TOKEN --channel CHANNEL [OPTIONS]

Required Arguments:
  --token          Slack Bot Token (xoxb-...)
  --channel        Channel ID (C...)

Optional Arguments:
  --output PATH    Output file path
  --format FORMAT  Output format: json, csv (default: json)
  --limit NUM      Max messages to fetch
  --start-time     Start time filter (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
  --end-time       End time filter
  --regex PATTERN  Regex pattern filter
  --case-sensitive Case sensitive regex
  --users USER...  Filter by user IDs
  --version        Show version
  --help           Show help
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any problems or have questions:

1. Check the [Issues](https://github.com/yourusername/slackdump/issues) page
2. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment details (Python version, OS, etc.)

## 🏆 Acknowledgments

- Built with the [Slack API](https://api.slack.com/)
- Inspired by the need for better Slack data export tools
- Thanks to all contributors and users