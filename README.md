# Telegram Bio Updater

Simple script that automatically updates your Telegram bio with quotes.

## Features

- Daily bio update
- Fixed time (MSK)
- No repeats (sequential quotes)
- Auto restart via systemd
- Logging

## Requirements

- Python 3.10+
- Telegram API (`api_id`, `api_hash`)

## Setup

1. Install dependencies:
```bash
pip install telethon
