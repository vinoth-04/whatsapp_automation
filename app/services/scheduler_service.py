import os
from datetime import datetime, timezone
from app.storage.csv_storage import mark_due_messages, update_message
from app.services.whatsapp_service import get_whatsapp_client


def check_due_messages():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking scheduled messages...")

    due_messages = mark_due_messages()

    if not due_messages:
        print("No messages are due.")
        return

    print(f"Found {len(due_messages)} due message(s). Starting dispatch...")

    headless = os.getenv("WHATSAPP_HEADLESS", "false").lower() == "true"
    client = get_whatsapp_client(headless=headless)

    for message in due_messages:
        msg_id = message["id"]
        phone = message["phone_number"]
        text = message["message"]

        print(f"--> Processing Message #{msg_id} to {phone}...")

        success, result = client.send_message(phone, text)

        if success:
            print(f"✅ Message #{msg_id} sent successfully! ID: {result}")
            update_message(
                msg_id,
                {
                    "status": "sent",
                    "provider_message_id": result,
                    "last_error": ""
                }
            )
        else:
            print(f"❌ Message #{msg_id} failed: {result}")
            update_message(
                msg_id,
                {
                    "status": "failed",
                    "last_error": result
                }
            )

    print("Finished processing due messages.")
