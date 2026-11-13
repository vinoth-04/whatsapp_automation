import csv
import os
import threading
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CSV_FILE = DATA_DIR / "scheduled_messages.csv"
TMP_FILE = DATA_DIR / "scheduled_messages.csv.tmp"
LOCK = threading.RLock()

FIELDS = [
    "id",
    "client_id",
    "phone_number",
    "message",
    "scheduled_at",
    "status",
    "recipient_opted_in",
    "provider_message_id",
    "last_error",
    "created_at"
]


def initialize_storage():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK:
        if not CSV_FILE.exists():
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=FIELDS, extrasaction="ignore")
                writer.writeheader()


def _read_messages_unlocked():
    if not CSV_FILE.exists():
        return []
    with open(CSV_FILE, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _save_messages_unlocked(messages):
    with open(TMP_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(messages)
    os.replace(TMP_FILE, CSV_FILE)


def read_messages():
    initialize_storage()
    with LOCK:
        return _read_messages_unlocked()


def save_messages(messages):
    initialize_storage()
    with LOCK:
        _save_messages_unlocked(messages)


def add_message(data):
    initialize_storage()
    with LOCK:
        messages = _read_messages_unlocked()

        next_id = max(
            (int(m["id"]) for m in messages if m.get("id") and m["id"].strip().isdigit()),
            default=0
        ) + 1

        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": str(next_id),
            "client_id": "local-demo",
            "phone_number": data.phone_number,
            "message": data.message,
            "scheduled_at": data.scheduled_at.astimezone(timezone.utc).isoformat(),
            "status": "scheduled",
            "recipient_opted_in": str(data.recipient_opted_in).lower(),
            "provider_message_id": "",
            "last_error": "",
            "created_at": now
        }

        messages.append(record)
        _save_messages_unlocked(messages)
        return record


def update_message(message_id, updates):
    initialize_storage()
    with LOCK:
        messages = _read_messages_unlocked()
        for message in messages:
            if message["id"] == str(message_id):
                message.update(updates)
                _save_messages_unlocked(messages)
                return message
        return None


def get_message(message_id):
    initialize_storage()
    with LOCK:
        messages = _read_messages_unlocked()
        for message in messages:
            if message["id"] == str(message_id):
                return message
        return None


def mark_due_messages():
    now = datetime.now(timezone.utc)
    due_messages = []

    with LOCK:
        messages = _read_messages_unlocked()
        for message in messages:
            if message.get("status") not in ("scheduled",):
                continue

            try:
                scheduled_time = datetime.fromisoformat(
                    message["scheduled_at"].replace("Z", "+00:00")
                )
                if scheduled_time.tzinfo is None:
                    scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)

                if scheduled_time <= now:
                    message["status"] = "ready"
                    due_messages.append(message.copy())
            except (ValueError, KeyError):
                continue

        if due_messages:
            _save_messages_unlocked(messages)

    return due_messages
